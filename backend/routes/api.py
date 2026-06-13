"""
/api/* — dashboard data endpoints (JWT protected).
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta, date

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import func, text

from .. import db
from ..models import Host, TrafficSnapshot, TrafficDaily, TrafficMonthly

api_bp = Blueprint("api", __name__)


def _fmt(n: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


# ── Hosts ─────────────────────────────────────────────────────────────────

@api_bp.get("/hosts")
@jwt_required()
def get_hosts():
    hosts = Host.query.filter_by(active=True).all()
    return jsonify([h.to_dict() for h in hosts])


# ── Overview: aggregate across all hosts ──────────────────────────────────

@api_bp.get("/overview")
@jwt_required()
def overview():
    hosts = Host.query.filter_by(active=True).all()
    host_ids = [h.id for h in hosts]

    # Total ever (from latest snapshot per host)
    totals = {"rx": 0, "tx": 0}
    live_rates = {"rx": 0, "tx": 0}
    host_status = []

    for host in hosts:
        latest = (TrafficSnapshot.query
                  .filter_by(host_id=host.id)
                  .order_by(TrafficSnapshot.captured_at.desc())
                  .first())
        if latest:
            totals["rx"] += latest.rx_total
            totals["tx"] += latest.tx_total
            live_rates["rx"] += latest.rx_rate
            live_rates["tx"] += latest.tx_rate
            age_sec = (datetime.now(timezone.utc) - latest.captured_at.replace(tzinfo=timezone.utc)).total_seconds()
            online = age_sec < 600  # offline if no push in 10 min
        else:
            online = False

        host_status.append({
            **host.to_dict(),
            "online": online,
            "rx_total": latest.rx_total if latest else 0,
            "tx_total": latest.tx_total if latest else 0,
            "rx_rate": latest.rx_rate if latest else 0,
            "tx_rate": latest.tx_rate if latest else 0,
            "rx_total_fmt": _fmt(latest.rx_total) if latest else "—",
            "tx_total_fmt": _fmt(latest.tx_total) if latest else "—",
            "rx_rate_fmt": _fmt(latest.rx_rate) + "/s" if latest else "—",
            "tx_rate_fmt": _fmt(latest.tx_rate) + "/s" if latest else "—",
        })

    # This month totals
    today = date.today()
    month_totals = (
        db.session.query(
            func.sum(TrafficMonthly.rx_bytes),
            func.sum(TrafficMonthly.tx_bytes)
        )
        .filter(
            TrafficMonthly.host_id.in_(host_ids),
            TrafficMonthly.year == today.year,
            TrafficMonthly.month == today.month,
        )
        .first()
    )

    return jsonify({
        "total_rx": totals["rx"],
        "total_tx": totals["tx"],
        "total_combined": totals["rx"] + totals["tx"],
        "total_rx_fmt": _fmt(totals["rx"]),
        "total_tx_fmt": _fmt(totals["tx"]),
        "total_combined_fmt": _fmt(totals["rx"] + totals["tx"]),
        "live_rx_rate": live_rates["rx"],
        "live_tx_rate": live_rates["tx"],
        "live_rx_fmt": _fmt(live_rates["rx"]) + "/s",
        "live_tx_fmt": _fmt(live_rates["tx"]) + "/s",
        "month_rx": month_totals[0] or 0,
        "month_tx": month_totals[1] or 0,
        "month_rx_fmt": _fmt(month_totals[0] or 0),
        "month_tx_fmt": _fmt(month_totals[1] or 0),
        "hosts": host_status,
        "host_count": len(hosts),
        "online_count": sum(1 for h in host_status if h["online"]),
    })


# ── Per-host detail ────────────────────────────────────────────────────────

@api_bp.get("/host/<host_name>")
@jwt_required()
def host_detail(host_name: str):
    host = Host.query.filter_by(name=host_name).first_or_404()

    # Last 24h snapshots (for live chart)
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    snaps = (TrafficSnapshot.query
             .filter(TrafficSnapshot.host_id == host.id,
                     TrafficSnapshot.captured_at >= since)
             .order_by(TrafficSnapshot.captured_at)
             .all())

    timeline = [
        {
            "t": s.captured_at.isoformat(),
            "rx": s.rx_bytes,
            "tx": s.tx_bytes,
            "rx_rate": s.rx_rate,
            "tx_rate": s.tx_rate,
        }
        for s in snaps
    ]

    # Last 30 days
    days_rows = (TrafficDaily.query
                 .filter_by(host_id=host.id)
                 .order_by(TrafficDaily.day.desc())
                 .limit(30).all())
    days = [{"date": str(d.day), "rx": d.rx_bytes, "tx": d.tx_bytes} for d in reversed(days_rows)]

    # Last 12 months
    months_rows = (TrafficMonthly.query
                   .filter_by(host_id=host.id)
                   .order_by(TrafficMonthly.year.desc(), TrafficMonthly.month.desc())
                   .limit(12).all())
    months = [
        {"label": f"{m.year}-{m.month:02d}", "rx": m.rx_bytes, "tx": m.tx_bytes}
        for m in reversed(months_rows)
    ]

    latest = (TrafficSnapshot.query
              .filter_by(host_id=host.id)
              .order_by(TrafficSnapshot.captured_at.desc())
              .first())

    return jsonify({
        "host": host.to_dict(),
        "timeline": timeline,
        "days": days,
        "months": months,
        "current": {
            "rx_total": latest.rx_total if latest else 0,
            "tx_total": latest.tx_total if latest else 0,
            "rx_rate": latest.rx_rate if latest else 0,
            "tx_rate": latest.tx_rate if latest else 0,
            "rx_total_fmt": _fmt(latest.rx_total) if latest else "—",
            "tx_total_fmt": _fmt(latest.tx_total) if latest else "—",
        } if latest else {},
    })


# ── Aggregated daily for all-hosts chart ─────────────────────────────────

@api_bp.get("/chart/daily")
@jwt_required()
def chart_daily():
    days_back = int(request.args.get("days", 30))
    host_ids_param = request.args.get("hosts", "")
    colors_rx = ["#38bdf8", "#34d399", "#a78bfa"]
    colors_tx = ["#f472b6", "#fb923c", "#facc15"]

    hosts_filter = Host.query.filter_by(active=True)
    if host_ids_param:
        names = [n.strip() for n in host_ids_param.split(",")]
        hosts_filter = hosts_filter.filter(Host.name.in_(names))
    active_hosts = hosts_filter.all()

    # Try traffic_daily first
    rows = db.session.query(
        TrafficDaily.day, Host.name, Host.display_name,
        TrafficDaily.rx_bytes, TrafficDaily.tx_bytes,
    ).join(Host, Host.id == TrafficDaily.host_id).filter(
        Host.active == True,
        TrafficDaily.day >= date.today() - timedelta(days=days_back),
    ).order_by(TrafficDaily.day).all()

    # Fallback: aggregate from snapshots grouped by day
    if not rows:
        rows_snap = db.session.query(
            func.date(TrafficSnapshot.captured_at).label("day"),
            Host.name,
            Host.display_name,
            func.max(TrafficSnapshot.rx_total).label("rx_bytes"),
            func.max(TrafficSnapshot.tx_total).label("tx_bytes"),
        ).join(Host, Host.id == TrafficSnapshot.host_id).filter(
            Host.active == True,
            TrafficSnapshot.captured_at >= datetime.now(timezone.utc) - timedelta(days=days_back),
        ).group_by(
            func.date(TrafficSnapshot.captured_at), Host.id
        ).order_by(text("day")).all()
        rows = rows_snap

    all_dates = sorted(set(str(r.day) for r in rows))
    hosts_seen = {}
    for r in rows:
        if r.name not in hosts_seen:
            hosts_seen[r.name] = {"name": r.name, "display": r.display_name, "rx": {}, "tx": {}}
        hosts_seen[r.name]["rx"][str(r.day)] = r.rx_bytes or 0
        hosts_seen[r.name]["tx"][str(r.day)] = r.tx_bytes or 0

    datasets = []
    for i, (name, d) in enumerate(hosts_seen.items()):
        datasets.append({
            "label": f"{d['display']} ↓",
            "host": name, "type": "rx",
            "data": [d["rx"].get(ds, 0) for ds in all_dates],
            "borderColor": colors_rx[i % len(colors_rx)],
            "backgroundColor": colors_rx[i % len(colors_rx)] + "22",
        })
        datasets.append({
            "label": f"{d['display']} ↑",
            "host": name, "type": "tx",
            "data": [d["tx"].get(ds, 0) for ds in all_dates],
            "borderColor": colors_tx[i % len(colors_tx)],
            "backgroundColor": colors_tx[i % len(colors_tx)] + "22",
        })

    return jsonify({"labels": all_dates, "datasets": datasets})


@api_bp.get("/chart/monthly")
@jwt_required()
def chart_monthly():
    rows = db.session.query(
        TrafficMonthly.year, TrafficMonthly.month,
        Host.name, Host.display_name,
        TrafficMonthly.rx_bytes, TrafficMonthly.tx_bytes,
    ).join(Host, Host.id == TrafficMonthly.host_id).filter(
        Host.active == True
    ).order_by(TrafficMonthly.year, TrafficMonthly.month).all()

    # Fallback: group snapshots by year-month using max(rx_total) per month
    if not rows:
        rows_snap = db.session.query(
            func.year(TrafficSnapshot.captured_at).label("year"),
            func.month(TrafficSnapshot.captured_at).label("month"),
            Host.name,
            Host.display_name,
            func.max(TrafficSnapshot.rx_total).label("rx_bytes"),
            func.max(TrafficSnapshot.tx_total).label("tx_bytes"),
        ).join(Host, Host.id == TrafficSnapshot.host_id).filter(
            Host.active == True
        ).group_by(
            func.year(TrafficSnapshot.captured_at),
            func.month(TrafficSnapshot.captured_at),
            Host.id,
        ).order_by(text("year, month")).all()
        rows = rows_snap

    labels = sorted(set(f"{r.year}-{r.month:02d}" for r in rows))
    hosts_seen = {}
    for r in rows:
        lbl = f"{r.year}-{r.month:02d}"
        if r.name not in hosts_seen:
            hosts_seen[r.name] = {"name": r.name, "display": r.display_name, "rx": {}, "tx": {}}
        hosts_seen[r.name]["rx"][lbl] = r.rx_bytes or 0
        hosts_seen[r.name]["tx"][lbl] = r.tx_bytes or 0

    datasets = []
    colors = ["#38bdf8", "#34d399", "#a78bfa"]
    for i, (name, d) in enumerate(hosts_seen.items()):
        c = colors[i % len(colors)]
        datasets.append({
            "label": d["display"],
            "rx": [d["rx"].get(l, 0) for l in labels],
            "tx": [d["tx"].get(l, 0) for l in labels],
            "color": c,
        })

    return jsonify({"labels": labels, "datasets": datasets})
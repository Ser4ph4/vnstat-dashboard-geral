"""
/api/collector/push — receives vnstat data from collector agents.
Authentication: X-Collector-Key header.
"""
from __future__ import annotations

from datetime import datetime, timezone, date

from flask import Blueprint, request, jsonify, current_app

from .. import db
from ..models import Host, TrafficSnapshot, TrafficDaily, TrafficMonthly

collector_bp = Blueprint("collector", __name__)


def _require_key():
    key = request.headers.get("X-Collector-Key", "")
    if key != current_app.config["COLLECTOR_API_KEY"]:
        return jsonify({"error": "Unauthorized"}), 401
    return None


@collector_bp.post("/push")
def push():
    err = _require_key()
    if err:
        return err

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No JSON body"}), 400

    host_name = data.get("host", "").strip()
    host = Host.query.filter_by(name=host_name).first()
    if not host:
        # Auto-register unknown hosts
        host = Host(name=host_name, display_name=host_name.capitalize())
        db.session.add(host)
        db.session.flush()

    now_utc = datetime.now(timezone.utc)
    host.last_seen = now_utc

    # ── Snapshot ─────────────────────────────────────────────────────────
    captured_at_str = data.get("captured_at")
    try:
        captured_at = datetime.fromisoformat(captured_at_str.replace("Z", "+00:00"))
    except Exception:
        captured_at = now_utc

    snap = TrafficSnapshot(
        host_id=host.id,
        captured_at=captured_at,
        rx_bytes=data.get("rx_hour", 0),
        tx_bytes=data.get("tx_hour", 0),
        rx_total=data.get("rx_total", 0),
        tx_total=data.get("tx_total", 0),
        rx_rate=data.get("rx_rate", 0),
        tx_rate=data.get("tx_rate", 0),
    )
    db.session.add(snap)

    # ── Daily upsert ─────────────────────────────────────────────────────
    for d in data.get("days", []):
        try:
            day = date.fromisoformat(d["date"])
        except Exception:
            continue
        existing = TrafficDaily.query.filter_by(host_id=host.id, day=day).first()
        if existing:
            existing.rx_bytes = d.get("rx", 0)
            existing.tx_bytes = d.get("tx", 0)
        else:
            db.session.add(TrafficDaily(
                host_id=host.id, day=day,
                rx_bytes=d.get("rx", 0), tx_bytes=d.get("tx", 0)
            ))

    # ── Monthly upsert ────────────────────────────────────────────────────
    for m in data.get("months", []):
        existing = TrafficMonthly.query.filter_by(
            host_id=host.id, year=m["year"], month=m["month"]
        ).first()
        if existing:
            existing.rx_bytes = m.get("rx", 0)
            existing.tx_bytes = m.get("tx", 0)
        else:
            db.session.add(TrafficMonthly(
                host_id=host.id, year=m["year"], month=m["month"],
                rx_bytes=m.get("rx", 0), tx_bytes=m.get("tx", 0)
            ))

    db.session.commit()
    return jsonify({"ok": True, "host": host_name}), 200


@collector_bp.get("/status")
def status():
    """Health-check for collector agents."""
    err = _require_key()
    if err:
        return err
    return jsonify({"ok": True, "ts": datetime.now(timezone.utc).isoformat()})

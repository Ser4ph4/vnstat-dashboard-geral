'''
Author: Ser4ph4
Date: 2026-06-13 01:23:11
LastEditors: Ser4ph4
LastEditTime: 2026-06-13 01:24:34
'''
from __future__ import annotations
from datetime import datetime, timezone

from . import db


class User(db.Model):
    __tablename__ = "users"
    id                = db.Column(db.Integer, primary_key=True)
    username          = db.Column(db.String(64), unique=True, nullable=False)
    password_hash     = db.Column(db.String(255), nullable=False)
    created_at        = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # ── CAMPOS PARA COMPATIBILIDADE COM 2FA (TOTP) ──────────────────
    # Guarda a chave secreta Base32 do autenticador
    two_factor_secret = db.Column(db.String(32), nullable=True)
    # Define se o 2FA já foi ativado e confirmado pelo usuário
    has_2fa_enabled   = db.Column(db.Boolean, default=False, server_default="0")


class Host(db.Model):
    __tablename__ = "hosts"
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(64), unique=True, nullable=False)
    display_name  = db.Column(db.String(128), nullable=False)
    tailscale_ip  = db.Column(db.String(45))
    interface     = db.Column(db.String(32), default="eth0")
    active        = db.Column(db.Boolean, default=True)
    created_at    = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_seen     = db.Column(db.DateTime, nullable=True)

    snapshots = db.relationship("TrafficSnapshot", back_populates="host",
                                 cascade="all, delete-orphan", lazy="dynamic")
    daily     = db.relationship("TrafficDaily", back_populates="host",
                                 cascade="all, delete-orphan", lazy="dynamic")
    monthly   = db.relationship("TrafficMonthly", back_populates="host",
                                 cascade="all, delete-orphan", lazy="dynamic")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "tailscale_ip": self.tailscale_ip,
            "interface": self.interface,
            "active": self.active,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
        }


class TrafficSnapshot(db.Model):
    __tablename__  = "traffic_snapshots"
    id          = db.Column(db.BigInteger, primary_key=True)
    host_id     = db.Column(db.Integer, db.ForeignKey("hosts.id"), nullable=False)
    captured_at = db.Column(db.DateTime, nullable=False, index=True)
    rx_bytes    = db.Column(db.BigInteger, default=0)
    tx_bytes    = db.Column(db.BigInteger, default=0)
    rx_total    = db.Column(db.BigInteger, default=0)
    tx_total    = db.Column(db.BigInteger, default=0)
    rx_rate     = db.Column(db.BigInteger, default=0)
    tx_rate     = db.Column(db.BigInteger, default=0)

    host = db.relationship("Host", back_populates="snapshots")

    __table_args__ = (
        db.Index("idx_host_time", "host_id", "captured_at"),
    )


class TrafficDaily(db.Model):
    __tablename__ = "traffic_daily"
    id       = db.Column(db.BigInteger, primary_key=True)
    host_id  = db.Column(db.Integer, db.ForeignKey("hosts.id"), nullable=False)
    day      = db.Column(db.Date, nullable=False, index=True)
    rx_bytes = db.Column(db.BigInteger, default=0)
    tx_bytes = db.Column(db.BigInteger, default=0)

    host = db.relationship("Host", back_populates="daily")

    __table_args__ = (
        db.UniqueConstraint("host_id", "day", name="uq_host_day"),
    )


class TrafficMonthly(db.Model):
    __tablename__ = "traffic_monthly"
    id       = db.Column(db.BigInteger, primary_key=True)
    host_id  = db.Column(db.Integer, db.ForeignKey("hosts.id"), nullable=False)
    year     = db.Column(db.SmallInteger, nullable=False)
    month    = db.Column(db.SmallInteger, nullable=False)
    rx_bytes = db.Column(db.BigInteger, default=0)
    tx_bytes = db.Column(db.BigInteger, default=0)

    host = db.relationship("Host", back_populates="monthly")

    __table_args__ = (
        db.UniqueConstraint("host_id", "year", "month", name="uq_host_month"),
    )
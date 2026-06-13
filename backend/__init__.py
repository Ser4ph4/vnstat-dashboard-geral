'''
Author: Ser4ph4
Date: 2026-06-13 04:58:27
LastEditors: Ser4ph4
LastEditTime: 2026-06-13 17:12:35
'''
from __future__ import annotations
import os
import secrets
from datetime import timedelta
from flask import Flask, send_from_directory
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
jwt = JWTManager()


def create_app(config_override: dict | None = None) -> Flask:
    # ── Mapeamento Dinâmico de Caminhos Absolutos (Correção para Docker) ──
    backend_dir = os.path.abspath(os.path.dirname(__file__))
    project_root = os.path.abspath(os.path.join(backend_dir, ".."))
    template_dir = os.path.join(project_root, "frontend", "templates")
    static_dir = os.path.join(project_root, "frontend", "static")

    # CORREÇÃO: Adicionado static_url_path para fixar a rota mapeada no Docker
    app = Flask(
        __name__, 
        template_folder=template_dir, 
        static_folder=static_dir,
        static_url_path='/static'
    )

    # ── Core config ─────────────────────────────────────────────────────
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", secrets.token_hex(32)),
        SQLALCHEMY_DATABASE_URI=os.getenv(
            "DATABASE_URL",
            "mysql+pymysql://vnstat:vnstat@db:3306/vnstat_dash"
        ),
        SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True, "pool_recycle": 300},
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY", secrets.token_hex(32)),
        JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=int(os.getenv("JWT_HOURS", "12"))),
        JWT_TOKEN_LOCATION=["cookies"],
        JWT_COOKIE_SECURE=os.getenv("FLASK_ENV") == "production",
        JWT_COOKIE_CSRF_PROTECT=False,   # SameSite=Lax covers CSRF for this use case
        COLLECTOR_API_KEY=os.getenv("COLLECTOR_API_KEY", "REPLACE_ME"),
    )

    if config_override:
        app.config.update(config_override)

    # ── Extensions ───────────────────────────────────────────────────────
    db.init_app(app)
    jwt.init_app(app)

    # ── Blueprints ────────────────────────────────────────────────────────
    from .routes.auth import auth_bp
    from .routes.api import api_bp
    from .routes.collector import collector_bp
    from .routes.pages import pages_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(collector_bp, url_prefix="/api/collector")
    app.register_blueprint(pages_bp)

    # ── ROTA EXPLÍCITA DO FAVICON (Corrigida para usar a pasta estática real) ──
    @app.route('/favicon.svg')
    def favicon():
        return send_from_directory(
            app.static_folder,
            'favicon.svg', 
            mimetype='image/svg+xml'
        )
        
    # ── First-run seed ────────────────────────────────────────────────────
    with app.app_context():
        db.create_all()
        _seed(app)

    return app


def _seed(app: Flask) -> None:
    from .models import User, Host
    from werkzeug.security import generate_password_hash

    admin_user = os.getenv("ADMIN_USER", "admin")
    admin_pass = os.getenv("ADMIN_PASS", "changeme")

    if not User.query.filter_by(username=admin_user).first():
        db.session.add(User(username=admin_user,
                            password_hash=generate_password_hash(admin_pass)))
        db.session.commit()
        app.logger.info("Seeded default admin user: %s", admin_user)

    # Seed hosts from env if provided
    hosts_env = os.getenv("HOSTS", "")
    if hosts_env:
        for entry in hosts_env.split(","):
            parts = entry.strip().split(":")
            if len(parts) >= 2:
                name, display = parts[0], parts[1]
                ip = parts[2] if len(parts) > 2 else None
                if not Host.query.filter_by(name=name).first():
                    db.session.add(Host(name=name, display_name=display,
                                        tailscale_ip=ip))
        db.session.commit()
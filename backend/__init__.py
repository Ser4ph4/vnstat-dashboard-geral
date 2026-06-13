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
    # ── Mapeamento Dinâmico de Caminhos Absolutos ─────────────────────────
    backend_dir = os.path.abspath(os.path.dirname(__file__))
    project_root = os.path.abspath(os.path.join(backend_dir, ".."))
    template_dir = os.path.join(project_root, "frontend", "templates")
    static_dir = os.path.join(project_root, "frontend", "static")

    # SOLUÇÃO: Desativamos o static padrão (None) para contornar o bloqueio de Jail do Flask
    app = Flask(__name__, template_folder=template_dir, static_folder=None)

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

    # ── ROTA MANUAL INFALÍVEL PARA OS ARQUIVOS ESTÁTICOS ──────────────────
    # Mantém o nome do endpoint como 'static' para não quebrar o url_for() do HTML
    @app.route('/static/<path:filename>', endpoint='static')
    def serve_static_custom(filename):
        return send_from_directory(static_dir, filename)

    # ── ROTA EXPLÍCITA DO FAVICON ─────────────────────────────────────────
    @app.route('/favicon.svg')
    def favicon():
        return send_from_directory(
            static_dir,
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
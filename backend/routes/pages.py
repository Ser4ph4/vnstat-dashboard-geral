from flask import Blueprint, render_template, redirect, url_for
from flask_jwt_extended import jwt_required, verify_jwt_in_request
from flask_jwt_extended.exceptions import NoAuthorizationError
from jwt.exceptions import InvalidTokenError

pages_bp = Blueprint("pages", __name__)


@pages_bp.get("/")
def index():
    try:
        verify_jwt_in_request()
        return redirect(url_for("pages.dashboard"))
    except Exception:
        return redirect(url_for("pages.login"))


@pages_bp.get("/login")
def login():
    return render_template("login.html")


@pages_bp.get("/dashboard")
def dashboard():
    try:
        verify_jwt_in_request()
    except Exception:
        return redirect(url_for("pages.login"))
    return render_template("dashboard.html")


@pages_bp.get("/host/<host_name>")
def host_detail(host_name: str):
    try:
        verify_jwt_in_request()
    except Exception:
        return redirect(url_for("pages.login"))
    return render_template("host.html", host_name=host_name)

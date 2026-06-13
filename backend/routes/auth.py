'''
Author: Ser4ph4
Date: 2026-06-13 01:21:35
LastEditors: Ser4ph4
LastEditTime: 2026-06-13 01:23:02
'''
from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import (
    create_access_token, set_access_cookies, unset_jwt_cookies,
    jwt_required, get_jwt_identity
)
from werkzeug.security import check_password_hash
import pyotp  # <--- IMPORTANTE: adicione o pyotp aqui

from ..models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/api/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Credenciais inválidas"}), 401

    # ── VERIFICAÇÃO DE 2FA ───────────────────────────────────────────
    # Se o usuário tiver o 2FA ativo, barramos o login direto aqui
    if getattr(user, 'has_2fa_enabled', False):
        return jsonify({"requires_2fa": True, "username": user.username}), 200

    # ── FLUXO NORMAL (SEM 2FA) ───────────────────────────────────────
    token = create_access_token(identity=str(user.id))
    resp = make_response(jsonify({"ok": True, "username": user.username}))
    set_access_cookies(resp, token)
    return resp


@auth_bp.post("/api/auth/verify-2fa")
def verify_2fa():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    token_2fa = data.get("token", "").strip()  # Token de 6 dígitos enviado pelo front

    if not username or not token_2fa:
        return jsonify({"error": "Dados insuficientes"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not getattr(user, 'two_factor_secret', None):
        return jsonify({"error": "Usuário inválido ou 2FA não configurado"}), 400

    # Instancia o TOTP usando o segredo salvo no banco para este usuário
    totp = pyotp.TOTP(user.two_factor_secret)
    
    # Valida o token (valid_window=1 dá tolerância de 30s para relógios atrasados)
    if not totp.verify(token_2fa, valid_window=1):
        return jsonify({"error": "Código 2FA inválido ou expirado"}), 401

    # Token correto! Agora sim geramos o JWT de acesso definitivo
    token = create_access_token(identity=str(user.id))
    resp = make_response(jsonify({"ok": True, "username": user.username}))
    set_access_cookies(resp, token)
    return resp


@auth_bp.post("/api/auth/logout")
@jwt_required()
def logout():
    resp = make_response(jsonify({"ok": True}))
    unset_jwt_cookies(resp)
    return resp


@auth_bp.get("/api/auth/me")
@jwt_required()
def me():
    uid = get_jwt_identity()
    user = User.query.get(int(uid))
    if not user:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"id": user.id, "username": user.username})
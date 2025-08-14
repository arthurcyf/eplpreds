# backend/routes/auth.py
from flask import Blueprint, request, jsonify
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user, UserMixin
)
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import select
from .. import db                    # <-- import from parent package (backend), not "."
from ..models import User            # <-- same here
import re

bp = Blueprint("auth", __name__)
login_manager = LoginManager()

USERNAME_RE = re.compile(r"^[a-z0-9_]{3,20}$")

class _User(UserMixin):
    def __init__(self, row: User):
        self.id = row.id
        self.email = row.email
        self.username = row.username

@login_manager.user_loader
def load_user(user_id):
    with db.SessionLocal() as s:
        u = s.get(User, int(user_id))
        return _User(u) if u else None

@bp.post("/auth/register")
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    pwd   = data.get("password") or ""
    uname = (data.get("username") or "").strip().lower() or None

    if not email or not pwd:
        return {"error": "email and password required"}, 400
    if uname and not USERNAME_RE.match(uname):
        return {"error": "invalid username (3-20: a-z, 0-9, _)"}, 400

    with db.SessionLocal() as s:
        if s.execute(select(User).where(User.email == email)).scalar_one_or_none():
            return {"error": "email already registered"}, 409
        if uname and s.execute(select(User).where(User.username == uname)).scalar_one_or_none():
            return {"error": "username taken"}, 409

        u = User(email=email, password_hash=generate_password_hash(pwd), username=uname)
        s.add(u)
        s.commit()

    return {"ok": True}

@bp.post("/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    pwd   = data.get("password") or ""

    with db.SessionLocal() as s:
        u = s.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if not u or not check_password_hash(u.password_hash, pwd):
            return jsonify({"error": "invalid credentials"}), 401
        login_user(_User(u))
        return jsonify({"ok": True})

@bp.post("/auth/logout")
@login_required
def logout():
    logout_user()
    return jsonify({"ok": True})

@bp.get("/auth/me")
@login_required
def me():
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
    }

@bp.post("/auth/username")
@login_required
def set_username():
    data = request.get_json(silent=True) or {}
    raw = (data.get("username") or "").strip().lower()

    if not USERNAME_RE.match(raw):
        return {"error": "invalid username (3-20: a-z, 0-9, _)"}, 400

    with db.SessionLocal() as s:
        exists = s.execute(
            select(User).where(User.username == raw, User.id != current_user.id)
        ).scalar_one_or_none()
        if exists:
            return {"error": "username taken"}, 409
        u = s.get(User, current_user.id)
        u.username = raw
        s.commit()

    return {"ok": True, "username": raw}

@bp.post("/auth/password")
@login_required
def change_password():
    """Body: { old_password: str, new_password: str }"""
    data = request.get_json(silent=True) or {}
    old_pw = (data.get("old_password") or data.get("current") or "").strip()
    new_pw = (data.get("new_password") or data.get("new") or "").strip()

    if len(new_pw) < 8:
        return {"error": "password must be at least 8 characters"}, 400

    with db.SessionLocal() as s:
        u = s.get(User, current_user.id)
        if not u or not check_password_hash(u.password_hash, old_pw):
            return {"error": "current password is incorrect"}, 401
        u.password_hash = generate_password_hash(new_pw)
        s.commit()

    return {"ok": True}
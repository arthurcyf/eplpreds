from flask import Blueprint, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import select
from .. import db
from ..models import User

bp = Blueprint("auth", __name__)
login_manager = LoginManager()

class _User(UserMixin):
    def __init__(self, row: User): self.id=row.id; self.email=row.email

@login_manager.user_loader
def load_user(user_id):
    with db.SessionLocal() as s:
        u = s.get(User, int(user_id))
        return _User(u) if u else None

@bp.post("/auth/register")
def register():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    pwd   = data.get("password") or ""
    if not email or not pwd: return jsonify({"error":"email/password required"}), 400
    with db.SessionLocal() as s:
        if s.execute(select(User).where(User.email==email)).scalar_one_or_none():
            return jsonify({"error":"email exists"}), 409
        u = User(email=email, password_hash=generate_password_hash(pwd))
        s.add(u); s.commit()
        return jsonify({"ok": True})

@bp.post("/auth/login")
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    pwd   = data.get("password") or ""
    with db.SessionLocal() as s:
        u = s.execute(select(User).where(User.email==email)).scalar_one_or_none()
        if not u or not check_password_hash(u.password_hash, pwd):
            return jsonify({"error":"invalid credentials"}), 401
        login_user(_User(u))
        return jsonify({"ok": True})

@bp.post("/auth/logout")
@login_required
def logout():
    logout_user()
    return jsonify({"ok": True})

@bp.get("/auth/me")
@login_required
def me(): return {"id": current_user.id}
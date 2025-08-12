import os, secrets
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import select, insert
from .. import db
from ..models import Group, GroupMember

bp = Blueprint("groups", __name__)

def _code(): return secrets.token_urlsafe(6)[:10]

@bp.post("/groups")
@login_required
def create_group():
    name = (request.json or {}).get("name")
    if not name: return {"error":"name required"}, 400
    with db.SessionLocal() as s:
        code = _code()
        g = Group(name=name, owner_id=current_user.id, invite_code=code)
        s.add(g); s.flush()
        s.add(GroupMember(group_id=g.id, user_id=current_user.id))
        s.commit()
        return {"ok": True, "group_id": g.id, "invite_code": code}

@bp.post("/groups/join")
@login_required
def join_group():
    code = (request.json or {}).get("code")
    if not code: return {"error":"code required"}, 400
    with db.SessionLocal() as s:
        g = s.execute(select(Group).where(Group.invite_code==code)).scalar_one_or_none()
        if not g: return {"error":"invalid code"}, 404
        exists = s.execute(select(GroupMember).where(
            GroupMember.group_id==g.id, GroupMember.user_id==current_user.id
        )).scalar_one_or_none()
        if not exists:
            s.add(GroupMember(group_id=g.id, user_id=current_user.id)); s.commit()
        return {"ok": True, "group_id": g.id, "group_name": g.name}
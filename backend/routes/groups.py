from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import select, text
from .. import db
from ..models import Group, GroupMember
import secrets

bp = Blueprint("groups", __name__)

def _code(): return secrets.token_urlsafe(6)[:10]

@bp.post("/groups")
@login_required
def create_group():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "My Group").strip()
    desc = (data.get("description") or "").strip()
    is_public = bool(data.get("is_public", False))
    join_policy = "public" if is_public else (data.get("join_policy") or "invite_only")
    with db.SessionLocal() as s:
        code = _code()
        g = Group(name=name, description=desc, owner_id=current_user.id,
                  invite_code=code, is_public=is_public, join_policy=join_policy)
        s.add(g); s.flush()
        s.add(GroupMember(group_id=g.id, user_id=current_user.id, status="approved"))
        s.commit()
        return {"ok": True, "group_id": g.id, "invite_code": code}

@bp.post("/groups/<int:group_id>/settings")
@login_required
def update_group_settings(group_id):
    data = request.get_json(silent=True) or {}
    with db.SessionLocal() as s:
        g = s.get(Group, group_id)
        if not g: return {"error":"not found"}, 404
        if g.owner_id != current_user.id: return {"error":"forbidden"}, 403
        if "name" in data: g.name = (data["name"] or "").strip() or g.name
        if "description" in data: g.description = (data["description"] or "").strip()
        if "is_public" in data:
            g.is_public = bool(data["is_public"])
            g.join_policy = "public" if g.is_public else "invite_only"
        if "join_policy" in data and data["join_policy"] in ("public","invite_only"):
            g.join_policy = data["join_policy"]; g.is_public = (g.join_policy=="public")
        s.commit()
        return {"ok": True, "group": {
            "id": g.id, "name": g.name, "description": g.description,
            "is_public": g.is_public, "join_policy": g.join_policy
        }}

@bp.post("/groups/join")
@login_required
def join_or_request():
    """Public group: auto-approve. Invite-only: create 'pending' request (admin must approve)."""
    data = request.get_json(silent=True) or {}
    code = (data.get("code") or "").strip()   # still support invite by code
    group_id = data.get("group_id")           # or direct group id (for public)
    with db.SessionLocal() as s:
        g = None
        if group_id:
            g = s.get(Group, int(group_id))
        if not g and code:
            g = s.execute(select(Group).where(Group.invite_code==code)).scalar_one_or_none()
        if not g: return {"error":"group not found"}, 404

        # already a member?
        gm = s.execute(select(GroupMember).where(
            GroupMember.group_id==g.id, GroupMember.user_id==current_user.id
        )).scalar_one_or_none()

        if gm:
            return {"ok": True, "group_id": g.id, "status": gm.status, "group_name": g.name}

        status = "approved" if g.join_policy=="public" else "pending"
        s.add(GroupMember(group_id=g.id, user_id=current_user.id, status=status))
        s.commit()
        return {"ok": True, "group_id": g.id, "status": status, "group_name": g.name}

@bp.get("/groups/<int:group_id>/requests")
@login_required
def list_requests(group_id):
    with db.SessionLocal() as s:
        g = s.get(Group, group_id)
        if not g: return {"error":"not found"}, 404
        if g.owner_id != current_user.id: return {"error":"forbidden"}, 403
        rows = s.execute(text("""
          select gm.user_id, u.email, gm.requested_at, gm.status
          from group_members gm join users u on u.id=gm.user_id
          where gm.group_id=:g and gm.status='pending'
          order by gm.requested_at asc
        """), {"g": group_id}).mappings().all()
    return {"pending": [dict(r) for r in rows]}

@bp.post("/groups/<int:group_id>/requests/<int:user_id>")
@login_required
def approve_or_reject(group_id, user_id):
    data = request.get_json(silent=True) or {}
    action = (data.get("action") or "").lower()  # 'approve' | 'reject'
    if action not in ("approve","reject"):
        return {"error":"action must be 'approve' or 'reject'"}, 400
    with db.SessionLocal() as s:
        g = s.get(Group, group_id)
        if not g: return {"error":"not found"}, 404
        if g.owner_id != current_user.id: return {"error":"forbidden"}, 403
        gm = s.execute(select(GroupMember).where(
            GroupMember.group_id==group_id, GroupMember.user_id==user_id
        )).scalar_one_or_none()
        if not gm: return {"error":"request not found"}, 404
        if gm.status != "pending": return {"error":"not pending"}, 400
        if action == "approve":
            s.execute(text("update group_members set status='approved', approved_at=now() where id=:id"), {"id": gm.id})
        else:
            s.execute(text("update group_members set status='rejected' where id=:id"), {"id": gm.id})
        s.commit()
    return {"ok": True, "action": action}

@bp.post("/groups/<int:group_id>/leave")
@login_required
def leave_group(group_id):
    with db.SessionLocal() as s:
        g = s.get(Group, group_id)
        if not g: return {"error":"not found"}, 404
        if g.owner_id == current_user.id:
            return {"error":"owner cannot leave; transfer ownership first"}, 400
        s.execute(text("delete from group_members where group_id=:g and user_id=:u"),
                  {"g": group_id, "u": current_user.id})
        s.commit()
    return {"ok": True}
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Date, Boolean, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .db import Base

class Match(Base):
    __tablename__ = "matches"
    match_id      = Column(BigInteger, primary_key=True)
    status        = Column(String(20))
    competition   = Column(String(40), nullable=False, default="Premier League")
    season        = Column(String(12), nullable=False)
    home          = Column(String(100), nullable=False)
    away          = Column(String(100), nullable=False)
    utc_kickoff   = Column(DateTime(timezone=True), nullable=False)
    local_kickoff = Column(DateTime(timezone=True), nullable=False)
    date          = Column(Date, nullable=False)
    time          = Column(String(5), nullable=False)
    home_score    = Column(Integer)
    away_score    = Column(Integer)
    updated_at    = Column(DateTime(timezone=True), nullable=False)

class User(Base):
    __tablename__ = "users"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    email        = Column(String(255), unique=True, nullable=False)
    password_hash= Column(String(255), nullable=False)
    created_at   = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    username     = Column(String(30), unique=True)  # nullable for existing users; enforce later

class Group(Base):
    __tablename__ = "groups"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    name         = Column(String(120), nullable=False)
    owner_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    invite_code  = Column(String(16), unique=True, nullable=False)
    description  = Column(Text)                                # NEW
    is_public    = Column(Boolean, nullable=False, default=False)  # NEW
    join_policy  = Column(String(32), nullable=False, default="invite_only")  # NEW: 'public'|'invite_only'
    created_at   = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

class GroupMember(Base):
    __tablename__ = "group_members"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    group_id     = Column(Integer, ForeignKey("groups.id"), nullable=False)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    status       = Column(String(16), nullable=False, default="approved")        # NEW
    requested_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))  # NEW
    approved_at  = Column(DateTime(timezone=True))                                # NEW
    UniqueConstraint("group_id", "user_id", name="uq_member")
    is_admin     = Column(Boolean, nullable=False, default=False)

class Prediction(Base):
    __tablename__ = "predictions"
    id        = Column(Integer, primary_key=True, autoincrement=True)
    group_id  = Column(Integer, ForeignKey("groups.id"), nullable=False)
    user_id   = Column(Integer, ForeignKey("users.id"), nullable=False)
    match_id  = Column(BigInteger, ForeignKey("matches.match_id"), nullable=False)
    home_pred = Column(Integer, nullable=False)
    away_pred = Column(Integer, nullable=False)
    created_at= Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at= Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    UniqueConstraint("group_id", "user_id", "match_id", name="uq_prediction")

class WeeklyScore(Base):
    __tablename__ = "weekly_scores"
    id        = Column(Integer, primary_key=True, autoincrement=True)
    group_id  = Column(Integer, ForeignKey("groups.id"), nullable=False)
    user_id   = Column(Integer, ForeignKey("users.id"), nullable=False)
    week_start= Column(Date, nullable=False)  # Thursday (local)
    points    = Column(Integer, nullable=False)
    updated_at= Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    UniqueConstraint("group_id", "user_id", "week_start", name="uq_weekly_score")
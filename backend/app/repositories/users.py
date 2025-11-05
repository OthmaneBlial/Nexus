from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlmodel import select

from ..db import get_session
from ..models import User


def create_user(email: str, display_name: str) -> User:
    with get_session() as session:
        statement = select(User).where(User.email == email)
        existing = session.exec(statement).one_or_none()
        if existing:
            return existing
        user = User(email=email, display_name=display_name)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def list_users() -> List[User]:
    with get_session() as session:
        statement = select(User).order_by(User.created_at.desc())
        return list(session.exec(statement))


def get_user(user_id: UUID) -> Optional[User]:
    with get_session() as session:
        statement = select(User).where(User.id == user_id)
        return session.exec(statement).one_or_none()

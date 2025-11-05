from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from ..repositories.users import create_user, get_user, list_users

router = APIRouter(prefix="/api/users", tags=["users"])


class CreateUserRequest(BaseModel):
    email: EmailStr
    displayName: str


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    displayName: str


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: CreateUserRequest) -> UserResponse:
    user = create_user(email=payload.email, display_name=payload.displayName)
    return UserResponse(id=user.id, email=user.email, displayName=user.display_name)


@router.get("", response_model=list[UserResponse])
def fetch_users() -> list[UserResponse]:
    return [
        UserResponse(id=user.id, email=user.email, displayName=user.display_name) for user in list_users()
    ]


@router.get("/{user_id}", response_model=UserResponse)
def fetch_user(user_id: UUID) -> UserResponse:
    user = get_user(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse(id=user.id, email=user.email, displayName=user.display_name)

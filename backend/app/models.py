from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class User(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)
    email: str = Field(index=True, unique=True, nullable=False)
    display_name: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)


class AnalysisReport(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)
    job_id: str = Field(index=True, unique=True, nullable=False)
    project_path: str = Field(nullable=False)
    status: AnalysisStatus = Field(default=AnalysisStatus.PENDING, nullable=False)
    summary: Optional[str] = Field(default=None)
    udm: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at: Optional[datetime] = Field(default=None)
    user_id: Optional[UUID] = Field(default=None, foreign_key="user.id")


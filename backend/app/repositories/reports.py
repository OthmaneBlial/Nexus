from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlmodel import select

from ..db import get_session
from ..models import AnalysisReport, AnalysisStatus


def create_report(job_id: str, project_path: str, user_id: Optional[UUID]) -> AnalysisReport:
    with get_session() as session:
        report = AnalysisReport(job_id=job_id, project_path=project_path, user_id=user_id)
        session.add(report)
        session.commit()
        session.refresh(report)
        return report


def update_report_status(
    job_id: str,
    status: AnalysisStatus,
    *,
    summary: Optional[str] = None,
    udm: Optional[dict] = None,
) -> None:
    with get_session() as session:
        statement = select(AnalysisReport).where(AnalysisReport.job_id == job_id)
        report = session.exec(statement).one_or_none()
        if report is None:
            return
        report.status = status
        if summary is not None:
            report.summary = summary
        if udm is not None:
            report.udm = udm
            report.completed_at = datetime.now(timezone.utc)
        elif status in {AnalysisStatus.FAILED}:
            report.completed_at = datetime.now(timezone.utc)
        session.add(report)
        session.commit()


def list_reports_for_user(user_id: UUID) -> List[AnalysisReport]:
    with get_session() as session:
        statement = (
            select(AnalysisReport)
            .where(AnalysisReport.user_id == user_id)
            .order_by(AnalysisReport.created_at.desc())
        )
        return list(session.exec(statement))


def get_report(job_id: str) -> Optional[AnalysisReport]:
    with get_session() as session:
        statement = select(AnalysisReport).where(AnalysisReport.job_id == job_id)
        return session.exec(statement).one_or_none()

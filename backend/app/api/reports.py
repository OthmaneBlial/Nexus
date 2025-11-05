from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from ..models import AnalysisStatus
from ..repositories.reports import get_report, list_reports_for_user

router = APIRouter(prefix="/api/reports", tags=["reports"])


class ReportSummary(BaseModel):
    jobId: str
    projectPath: str
    status: AnalysisStatus
    summary: Optional[str] = None
    createdAt: datetime
    completedAt: Optional[datetime] = None


class ReportDetail(ReportSummary):
    udm: Optional[dict] = None


@router.get("/user/{user_id}", response_model=list[ReportSummary])
def reports_for_user(user_id: UUID) -> list[ReportSummary]:
    reports = list_reports_for_user(user_id)
    return [
        ReportSummary(
            jobId=report.job_id,
            projectPath=report.project_path,
            status=report.status,
            summary=report.summary,
            createdAt=report.created_at,
            completedAt=report.completed_at,
        )
        for report in reports
    ]


@router.get("/{job_id}", response_model=ReportDetail)
def report_detail(job_id: str, include_udm: bool = Query(default=True)) -> ReportDetail:
    report = get_report(job_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return ReportDetail(
        jobId=report.job_id,
        projectPath=report.project_path,
        status=report.status,
        summary=report.summary,
        createdAt=report.created_at,
        completedAt=report.completed_at,
        udm=report.udm if include_udm else None,
    )

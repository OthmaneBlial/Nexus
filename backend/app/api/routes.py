from __future__ import annotations

import logging
import os
from uuid import UUID, uuid4

from celery.result import AsyncResult
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status
from pydantic import BaseModel

from ..repositories.reports import create_report, get_report as get_report_record
from ..repositories.users import get_user
from ..security import get_allowed_root, list_directory, resolve_path
from ..tasks import JobStatus, celery_app, execute_analysis_task, map_celery_state, perform_analysis

router = APIRouter(prefix="/api", tags=["nexus"])
LOGGER = logging.getLogger(__name__)


class FilesystemEntry(BaseModel):
    name: str
    path: str
    type: str


class FilesystemResponse(BaseModel):
    path: str
    entries: list[FilesystemEntry]


class AnalyzeRequest(BaseModel):
    projectPath: str
    userId: UUID | None = None


class AnalyzeResponse(BaseModel):
    jobId: str


class JobStatusResponse(BaseModel):
    status: JobStatus
    progress: int
    message: str | None = None
    error: str | None = None


@router.get("/filesystem", response_model=FilesystemResponse)
def browse_filesystem(path: str | None = Query(default=None)) -> FilesystemResponse:
    target = resolve_path(path)
    entries = [FilesystemEntry(**entry) for entry in list_directory(target)]
    root = get_allowed_root()
    relative = "." if target == root else str(target.relative_to(root))
    return FilesystemResponse(path=relative, entries=entries)


TASK_MODE = os.getenv("NEXUS_TASK_MODE", "celery").lower()


@router.post("/analyze", response_model=AnalyzeResponse, status_code=status.HTTP_202_ACCEPTED)
def start_analysis(request: AnalyzeRequest, background_tasks: BackgroundTasks) -> AnalyzeResponse:
    project_path = resolve_path(request.projectPath)
    user_id = None
    if request.userId:
        user = get_user(request.userId)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        user_id = user.id
    resolved_path = str(project_path)

    if TASK_MODE == "celery":
        async_result = execute_analysis_task.delay(resolved_path)
        create_report(async_result.id, resolved_path, user_id)
        return AnalyzeResponse(jobId=async_result.id)

    job_id = uuid4().hex
    create_report(job_id, resolved_path, user_id)
    background_tasks.add_task(run_inline_analysis, job_id, resolved_path)
    return AnalyzeResponse(jobId=job_id)


@router.get("/status/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str) -> JobStatusResponse:
    if TASK_MODE != "celery":
        report = get_report_record(job_id)
        if report is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        status_value = JobStatus(report.status.value)
        progress = 100 if status_value == JobStatus.COMPLETED else (50 if status_value == JobStatus.RUNNING else 0)
        return JobStatusResponse(
            status=status_value,
            progress=progress,
            message=report.summary,
            error=report.summary if status_value == JobStatus.FAILED else None,
        )
    result = AsyncResult(job_id, app=celery_app)
    payload = map_celery_state(result)
    return JobStatusResponse(
        status=payload["status"],
        progress=payload["progress"],
        message=payload["message"],
        error=payload["error"],
    )


@router.get("/report/{job_id}")
def get_report(job_id: str):
    if TASK_MODE != "celery":
        report = get_report_record(job_id)
        if report is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
        status_value = JobStatus(report.status.value)
        if status_value == JobStatus.FAILED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=report.summary or "Analysis failed")
        if status_value == JobStatus.COMPLETED and report.udm:
            return report.udm
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not ready")
    result = AsyncResult(job_id, app=celery_app)
    if result.failed():
        detail = str(result.info) if result.info else "Analysis failed"
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    if not result.ready():
        stored = get_report_record(job_id)
        if stored and stored.udm:
            return stored.udm
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not ready")

    data = result.result
    if data is None:
        stored = get_report_record(job_id)
        if stored and stored.udm:
            return stored.udm
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report unavailable")

    return data


def run_inline_analysis(job_id: str, project_path: str) -> None:
    try:
        perform_analysis(job_id, project_path)
    except Exception as exc:  # pragma: no cover - defensive
        # perform_analysis already records failure status; just log
        LOGGER = logging.getLogger(__name__)
        LOGGER.exception("Inline analysis failed for %s: %s", project_path, exc)

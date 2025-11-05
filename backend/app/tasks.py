from __future__ import annotations

import logging
import sys
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

from celery import states
from celery.result import AsyncResult

from .celery_app import celery_app
from .core.orchestrator import AnalysisError, AnalysisOrchestrator
from .models import AnalysisStatus
from .repositories.reports import update_report_status

LOGGER = logging.getLogger(__name__)


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


PY_PLUGIN_SRC = Path(__file__).resolve().parents[2] / "plugins" / "python_analyzer" / "src"
JS_PLUGIN_SRC = Path(__file__).resolve().parents[2] / "plugins" / "javascript_analyzer" / "src"
JAVA_PLUGIN_SRC = Path(__file__).resolve().parents[2] / "plugins" / "java_analyzer" / "src"

for plugin_src in (PY_PLUGIN_SRC, JS_PLUGIN_SRC, JAVA_PLUGIN_SRC):
    if plugin_src.exists():
        plugin_path = str(plugin_src)
        if plugin_path not in sys.path:
            sys.path.append(plugin_path)

orchestrator = AnalysisOrchestrator()

try:
    from nexus_analyzer_python.plugin import PythonAnalyzer

    orchestrator.plugin_manager.register(PythonAnalyzer())
except ModuleNotFoundError:
    LOGGER.warning("Python analyzer plugin is not available on PYTHONPATH.")

try:
    from nexus_analyzer_javascript.plugin import JavaScriptAnalyzer

    orchestrator.plugin_manager.register(JavaScriptAnalyzer())
except ModuleNotFoundError:
    LOGGER.warning("JavaScript analyzer plugin is not available on PYTHONPATH.")

try:
    from nexus_analyzer_java.plugin import JavaAnalyzer

    orchestrator.plugin_manager.register(JavaAnalyzer())
except ModuleNotFoundError:
    LOGGER.warning("Java analyzer plugin is not available on PYTHONPATH.")


@celery_app.task(bind=True, name="nexus.execute_analysis", autoretry_for=(), retry_backoff=False)
def execute_analysis_task(self, project_path: str) -> Dict[str, Any]:
    """Celery task that runs the Nexus orchestrator."""
    job_id = self.request.id
    payload = perform_analysis(job_id, project_path, progress_callback=self.update_state)
    return payload


def perform_analysis(job_id: str, project_path: str, progress_callback=None) -> Dict[str, Any]:
    LOGGER.info("Starting analysis for %s", project_path)
    update_report_status(job_id, AnalysisStatus.RUNNING, summary="Analyzer started")
    if progress_callback:
        progress_callback(state="PROGRESS", meta={"progress": 10, "message": "Preparing analyzers"})
    try:
        udm = orchestrator.analyze(project_path)
        if progress_callback:
            progress_callback(state="PROGRESS", meta={"progress": 85, "message": "Preparing report"})
        payload = udm.model_dump(mode="json", by_alias=True)
        update_report_status(job_id, AnalysisStatus.COMPLETED, summary="Analysis completed", udm=payload)
        LOGGER.info("Completed analysis for %s", project_path)
        return payload
    except (AnalysisError, FileNotFoundError, NotADirectoryError) as exc:
        LOGGER.exception("Analysis failed for %s: %s", project_path, exc)
        update_report_status(job_id, AnalysisStatus.FAILED, summary=str(exc))
        raise exc
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.exception("Unexpected failure for %s: %s", project_path, exc)
        update_report_status(job_id, AnalysisStatus.FAILED, summary=str(exc))
        raise exc


def map_celery_state(result: AsyncResult) -> dict[str, Optional[Any]]:
    """Translate Celery AsyncResult state into API-friendly response."""
    state = result.state
    info = result.info if isinstance(result.info, dict) else {}

    if state in {states.PENDING, states.RECEIVED, states.QUEUED}:
        mapped_state = JobStatus.PENDING
        progress = 0
        message = "Queued for analysis"
        error = None
    elif state in {states.STARTED, "PROGRESS"}:
        mapped_state = JobStatus.RUNNING
        progress = int(info.get("progress", 25))
        message = str(info.get("message") or "Analyzer running")
        error = None
    elif state == states.SUCCESS:
        mapped_state = JobStatus.COMPLETED
        progress = 100
        message = "Analysis completed"
        error = None
    elif state in {states.FAILURE, states.REVOKED}:
        mapped_state = JobStatus.FAILED
        progress = int(info.get("progress", 0))
        message = str(info.get("message") or "Analysis failed")
        error = str(result.info) if result.info else message
    else:
        mapped_state = JobStatus.PENDING
        progress = 0
        message = "Pending"
        error = None

    return {
        "status": mapped_state,
        "progress": progress,
        "message": message,
        "error": error,
    }


__all__ = ["execute_analysis_task", "celery_app", "JobStatus", "map_celery_state", "perform_analysis"]

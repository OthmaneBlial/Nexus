from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .plugins import PluginManager
from .udm import UnifiedDataModel


class AnalysisError(RuntimeError):
    """Base exception for analysis failures."""


class PluginNotFoundError(AnalysisError):
    """Raised when no analyzer plugin can handle the project."""


class AnalysisOrchestrator:
    """Coordinates analyzer discovery and execution."""

    def __init__(self, plugin_manager: Optional[PluginManager] = None) -> None:
        self.plugin_manager = plugin_manager or PluginManager()

    def analyze(self, project_path: str) -> UnifiedDataModel:
        normalized = self._normalize_path(project_path)
        applicable_plugins = self.plugin_manager.find_applicable(str(normalized))
        if not applicable_plugins:
            raise PluginNotFoundError(f"No analyzer plugin supports {normalized}")

        # Milestone 1: run the first suitable plugin.
        plugin = applicable_plugins[0]
        raw_udm = plugin.analyze(str(normalized))
        payload = self._ensure_payload(raw_udm, project_path=str(normalized), plugin_name=plugin.name)
        return UnifiedDataModel.model_validate(payload)

    def _normalize_path(self, project_path: str) -> Path:
        path = Path(project_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"Project path {project_path} does not exist")
        if not path.is_dir():
            raise NotADirectoryError(f"Project path {project_path} is not a directory")
        return path

    def _ensure_payload(self, payload: dict, *, project_path: str, plugin_name: str) -> dict:
        if not isinstance(payload, dict):
            raise AnalysisError("Analyzer plugins must return a dictionary payload")

        path = Path(project_path)
        timestamp = datetime.now(timezone.utc)

        merged = {
            "projectName": path.name,
            "analysisTimestamp": timestamp,
            "languages": [plugin_name],
        }
        merged.update(payload)

        languages = merged.get("languages")
        if not languages:
            merged["languages"] = [plugin_name]
        elif isinstance(languages, str):
            merged["languages"] = [languages]

        if "analysisTimestamp" not in payload:
            merged["analysisTimestamp"] = timestamp

        return merged

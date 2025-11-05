from __future__ import annotations

import logging
from importlib.metadata import entry_points
from typing import Dict, List, Optional, Sequence

from .analyzer import AnalyzerPlugin

LOGGER = logging.getLogger(__name__)
NEXUS_ANALYZER_GROUP = "nexus.analyzers"


class PluginManager:
    """Discovers and manages analyzer plugins."""

    def __init__(self) -> None:
        self._plugins: Dict[str, AnalyzerPlugin] = {}
        self._load_entry_point_plugins()

    @property
    def plugins(self) -> Sequence[AnalyzerPlugin]:
        return tuple(self._plugins.values())

    def register(self, plugin: AnalyzerPlugin) -> None:
        if plugin.name in self._plugins:
            LOGGER.debug("Plugin %s already registered, skipping.", plugin.name)
            return
        self._plugins[plugin.name] = plugin

    def _load_entry_point_plugins(self) -> None:
        try:
            eps = entry_points().select(group=NEXUS_ANALYZER_GROUP)  # type: ignore[attr-defined]
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.error("Failed loading entry points: %s", exc)
            return

        for ep in eps:
            try:
                plugin_candidate = ep.load()
            except Exception as exc:
                LOGGER.exception("Failed loading plugin %s: %s", ep.name, exc)
                continue

            plugin = self._coerce_plugin(plugin_candidate)
            if plugin is None:
                LOGGER.warning("Entry point %s is not a valid AnalyzerPlugin.", ep.name)
                continue

            self.register(plugin)

    def _coerce_plugin(self, candidate) -> Optional[AnalyzerPlugin]:
        if isinstance(candidate, AnalyzerPlugin):
            return candidate

        if isinstance(candidate, type) and issubclass(candidate, AnalyzerPlugin):
            try:
                return candidate()
            except Exception as exc:
                LOGGER.exception("Failed instantiating plugin %s: %s", candidate, exc)
                return None

        if callable(candidate):
            try:
                produced = candidate()
            except Exception as exc:
                LOGGER.exception("Callable plugin factory failed: %s", exc)
                return None
            return self._coerce_plugin(produced)

        return None

    def find_applicable(self, project_path: str) -> List[AnalyzerPlugin]:
        """Return all plugins that report support for path."""
        applicable = []
        for plugin in self._plugins.values():
            try:
                if plugin.discover(project_path):
                    applicable.append(plugin)
            except Exception as exc:
                LOGGER.exception("Plugin %s discover() failed: %s", plugin.name, exc)
        return applicable

    def get_plugin(self, name: str) -> Optional[AnalyzerPlugin]:
        return self._plugins.get(name)

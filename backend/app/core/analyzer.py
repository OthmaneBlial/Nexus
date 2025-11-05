from __future__ import annotations

from abc import ABC, abstractmethod


class AnalyzerPlugin(ABC):
    """Contract shared by all analyzer plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-friendly name describing the analyzer."""

    @abstractmethod
    def discover(self, path: str) -> bool:
        """Return True when the plugin can handle the project at path."""

    @abstractmethod
    def analyze(self, path: str) -> dict:
        """Perform the analysis and return a UDM-compatible dictionary."""

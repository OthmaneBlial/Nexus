from __future__ import annotations

import os
from pathlib import Path

from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_filesystem_listing(client: TestClient, tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "project").mkdir()
    (tmp_path / "project" / "pyproject.toml").write_text("[tool.poetry]\nname='demo'\n")
    monkeypatch.setenv("NEXUS_ALLOWED_ROOT", str(tmp_path))

    response = client.get("/api/filesystem")
    assert response.status_code == 200
    payload = response.json()
    assert payload["path"] == "."
    assert any(entry["name"] == "project" for entry in payload["entries"])

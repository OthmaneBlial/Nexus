from __future__ import annotations

import os
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("NEXUS_DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("NEXUS_ALLOWED_ROOT", os.getcwd())

from app.main import app  # noqa: E402
from app.db import init_db  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def setup_database() -> None:
    init_db()


@pytest.fixture(scope="function")
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client

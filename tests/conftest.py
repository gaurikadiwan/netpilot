from __future__ import annotations

import os

import pytest

# Point the app at an isolated SQLite DB before any app module is imported.
os.environ["DATABASE_URL"] = "sqlite:///./test_netpilot.db"
os.environ["NETPILOT_API_TOKEN"] = "test-token"
os.environ["NETPILOT_TOKEN_SCOPES"] = "read,plan"
os.environ["AUDIT_LOG_PATH"] = "./test_audit.log"

from fastapi.testclient import TestClient

from mcp_server.main import app
from network_sim.database import init_db
from network_sim.seed import seed


@pytest.fixture(scope="session", autouse=True)
def _seeded_db():
    # Guard against a leftover DB file from a previous crashed run colliding
    # with seed()'s unique node names.
    if os.path.exists("./test_netpilot.db"):
        os.remove("./test_netpilot.db")
    init_db()
    seed()
    yield
    for path in ("./test_netpilot.db", "./test_audit.log"):
        if os.path.exists(path):
            os.remove(path)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def auth_headers() -> dict:
    return {"Authorization": "Bearer test-token"}

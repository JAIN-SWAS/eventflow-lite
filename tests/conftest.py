import os
import sys
from pathlib import Path

# Set env BEFORE importing app
os.environ.setdefault("REDIS_URL", "redis://127.0.0.1:6379/0")
os.environ.setdefault("DATABASE_URL", "sqlite:///./data/test_eventflow.db")
os.environ.setdefault("ENV", "test")
os.environ.setdefault("EVENTFLOW_SYNC_TASKS", "1")

# Ensure local folder exists
Path("data").mkdir(exist_ok=True)

# Optional: reset test DB each run (clean slate)
test_db = Path("data/test_eventflow.db")
if test_db.exists():
    test_db.unlink()

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest  # noqa: E402
from app.db import init_db  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Initialize database tables before running any tests."""
    init_db()
    yield

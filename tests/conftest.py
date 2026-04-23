from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.auth import get_user_by_username
from app.seed import seed_demo_data


@pytest.fixture()
def seeded_db(tmp_path, monkeypatch):
    monkeypatch.setenv("LIGHTHOUSE_DB_PATH", str(tmp_path / "lighthouse-test.db"))
    counts = seed_demo_data(reset=True)
    return {
        "counts": counts,
        "reporter": get_user_by_username("reporter01"),
        "analyst": get_user_by_username("analyst01"),
        "admin": get_user_by_username("admin01"),
    }

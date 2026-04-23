from __future__ import annotations

from app.database import get_connection


def test_alert_schema_includes_reporter_redesign_columns(seeded_db):
    with get_connection() as connection:
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(alerts)").fetchall()
        }

    assert "occurred_at" in columns
    assert "location" in columns
    assert "attachments_json" in columns

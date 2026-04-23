from __future__ import annotations

import pytest

from app.services.metrics import get_dashboard_metrics


def test_dashboard_metrics_match_seeded_dataset(seeded_db):
    admin = seeded_db["admin"]
    metrics = get_dashboard_metrics(admin)
    totals = metrics["totals"]

    assert totals["total_alerts"] == 6
    assert totals["total_incidents"] == 6
    assert totals["open_incidents"] == 4
    assert totals["critical_incidents"] == 4
    assert totals["escalations"] == 1
    assert totals["mean_triage_minutes"] > 0
    assert totals["false_positive_rate"] == pytest.approx(16.7, abs=0.1)

    assert any(item["severity"] == "High" for item in metrics["alerts_by_severity"])
    assert any(item["status"] == "New" for item in metrics["status_breakdown"])

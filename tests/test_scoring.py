from __future__ import annotations

from app.services.scoring import derive_confidence, score_incident


def test_scoring_promotes_critical_privileged_activity_to_p1():
    result = score_incident("Critical", "High", "Critical", "Privileged")
    assert result["score"] == 13
    assert result["priority"] == "P1"


def test_scoring_keeps_medium_standard_activity_lower_priority():
    confidence = derive_confidence("Unknown", 0)
    result = score_incident("Medium", confidence, "Medium", "Standard")
    assert confidence == "Low"
    assert result["score"] == 5
    assert result["priority"] == "P4"

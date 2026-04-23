from __future__ import annotations

from datetime import date, time
from types import SimpleNamespace

from app.ui.reporter import _resolve_attachment_draft, combine_occurrence_timestamp, validate_reporter_wizard_step


def test_combine_occurrence_timestamp_returns_iso_minutes():
    result = combine_occurrence_timestamp(date(2026, 4, 23), time(10, 43))
    assert result == "2026-04-23T10:43"


def test_step_one_validation_requires_core_fields():
    errors = validate_reporter_wizard_step(
        1,
        {
            "alert_type": "",
            "severity_estimate": "",
            "occurred_on": None,
            "occurred_time": None,
            "description": "",
        },
    )
    assert len(errors) == 4


def test_step_two_validation_requires_contact_information():
    errors = validate_reporter_wizard_step(
        2,
        {
            "contact_info": "",
        },
    )
    assert errors == ["Contact information is required so the SOC team can follow up."]


def test_resolve_attachment_draft_preserves_existing_metadata_when_uploader_is_unmounted():
    existing = [{"name": "triage-screenshot.png", "size": 4096, "type": "image/png"}]

    assert _resolve_attachment_draft(None, existing) == existing


def test_resolve_attachment_draft_prefers_current_upload_selection():
    existing = [{"name": "older-note.txt", "size": 128, "type": "text/plain"}]
    upload = SimpleNamespace(name="fresh-capture.png", size=8192, type="image/png")

    result = _resolve_attachment_draft([upload], existing)

    assert result == [{"name": "fresh-capture.png", "size": 8192, "type": "image/png"}]

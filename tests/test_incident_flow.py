from __future__ import annotations

from datetime import date, time

from app.services.incidents import add_note, assign_incident, escalate_incident, get_incident, update_status
from app.services.intake import create_alert, get_alert, list_reporter_alerts


def test_reporter_alert_creation_opens_incident_and_supports_lifecycle(seeded_db):
    reporter = seeded_db["reporter"]
    analyst = seeded_db["analyst"]

    created = create_alert(
        reporter,
        {
            "alert_type": "Phishing Reported",
            "severity_estimate": "Medium",
            "description": "Finance user reported a suspicious invoice email.",
            "affected_user": "olivia.chen",
            "affected_asset": "FIN-WS-01",
            "source_ip": "203.0.113.19",
            "evidence_name": "invoice_sample.eml",
            "contact_info": "mia.santos@lighthouse.demo",
            "occurred_at": "2026-04-22T09:45",
            "location": "Melbourne, Australia",
            "attachments": [
                {
                    "name": "invoice_sample.eml",
                    "size": 98304,
                    "type": "message/rfc822",
                }
            ],
        },
    )

    reporter_alerts = list_reporter_alerts(reporter)
    assert any(alert["alert_id"] == created["alert_id"] for alert in reporter_alerts)
    assert created["occurred_at"] == "2026-04-22T09:45"
    assert created["location"] == "Melbourne, Australia"
    assert created["attachment_count"] == 1

    incident = get_incident(created["incident_id"], analyst)
    assert incident["priority"] in {"P1", "P2", "P3", "P4", "P5"}
    assert incident["playbook"]["alert_type"] == "Phishing Reported"

    assigned = assign_incident(created["incident_id"], "analyst01", analyst)
    assert assigned["assignee_username"] == "analyst01"

    note = add_note(
        created["incident_id"],
        analyst,
        "User confirmed no click and mail was quarantined.",
        visible_to_reporter=True,
    )
    assert note["visible_to_reporter"] == 1

    escalated = escalate_incident(created["incident_id"], analyst, "Escalating for leadership visibility.")
    assert escalated["incident_status"] == "Escalated"
    assert escalated["escalation_level"] == 1

    closed = update_status(created["incident_id"], "Closed", analyst)
    assert closed["incident_status"] == "Closed"

    reporter_view = get_alert(created["alert_id"], reporter)
    assert any("quarantined" in note["content"] for note in reporter_view["notes"])
    assert reporter_view["attachments"][0]["name"] == "invoice_sample.eml"

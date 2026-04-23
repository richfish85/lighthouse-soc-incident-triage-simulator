"""Database seeding helpers for Lighthouse SOC."""

from __future__ import annotations

import json
from pathlib import Path

from app.database import get_connection, init_db, reset_db


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"


def load_json_file(filename: str) -> object:
    """Read a project JSON file from the data directory."""
    with (DATA_DIR / filename).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def seed_demo_data(reset: bool = False) -> dict[str, int]:
    """Populate the SQLite database with deterministic demo data."""
    if reset:
        reset_db()
    else:
        init_db()

    with get_connection() as connection:
        existing_users = connection.execute("SELECT COUNT(*) AS total FROM users").fetchone()["total"]
        if existing_users and not reset:
            return {
                "users": existing_users,
                "alerts": connection.execute("SELECT COUNT(*) AS total FROM alerts").fetchone()["total"],
                "incidents": connection.execute("SELECT COUNT(*) AS total FROM incidents").fetchone()["total"],
                "playbooks": connection.execute("SELECT COUNT(*) AS total FROM playbooks").fetchone()["total"],
            }

        users_payload = load_json_file("sample_users.json")
        alerts_payload = load_json_file("sample_alerts.json")
        playbooks_payload = load_json_file("sample_playbooks.json")

        connection.execute("DELETE FROM audit_log")
        connection.execute("DELETE FROM notes")
        connection.execute("DELETE FROM enrichment")
        connection.execute("DELETE FROM incidents")
        connection.execute("DELETE FROM alerts")
        connection.execute("DELETE FROM playbooks")
        connection.execute("DELETE FROM users")

        user_lookup: dict[str, int] = {}
        for user in users_payload["app_users"]:
            cursor = connection.execute(
                """
                INSERT INTO users (username, full_name, role, email, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user["username"],
                    user["full_name"],
                    user["role"],
                    user["email"],
                    int(user.get("is_active", True)),
                    user["created_at"],
                ),
            )
            user_lookup[user["username"]] = int(cursor.lastrowid)

        for playbook in playbooks_payload:
            connection.execute(
                """
                INSERT INTO playbooks (alert_type, title, steps_json, severity_hint, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    playbook["alert_type"],
                    playbook["title"],
                    json.dumps(playbook["steps"]),
                    playbook["severity_hint"],
                    playbook["created_at"],
                ),
            )

        for alert in alerts_payload:
            reporter_id = user_lookup[alert["reporter_username"]]
            connection.execute(
                """
                INSERT INTO alerts (
                    alert_id,
                    reporter_user_id,
                    alert_type,
                    severity_estimate,
                    description,
                    affected_user,
                    affected_asset,
                    source_ip,
                    evidence_name,
                    occurred_at,
                    location,
                    attachments_json,
                    contact_info,
                    raw_payload,
                    status,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    alert["alert_id"],
                    reporter_id,
                    alert["alert_type"],
                    alert["severity_estimate"],
                    alert["description"],
                    alert["affected_user"],
                    alert["affected_asset"],
                    alert["source_ip"],
                    alert["evidence_name"],
                    alert.get("occurred_at"),
                    alert.get("location"),
                    json.dumps(alert.get("attachments", [])),
                    alert["contact_info"],
                    json.dumps(alert["raw_payload"]),
                    alert["status"],
                    alert["created_at"],
                    alert["updated_at"],
                ),
            )

            incident = alert["incident"]
            assigned_to = incident.get("assigned_to")
            assigned_to_id = user_lookup[assigned_to] if assigned_to else None
            connection.execute(
                """
                INSERT INTO incidents (
                    incident_id,
                    alert_id,
                    severity,
                    confidence,
                    priority,
                    assigned_to,
                    escalation_level,
                    incident_status,
                    mitre_tactic,
                    event_count,
                    created_at,
                    updated_at,
                    closed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    incident["incident_id"],
                    alert["alert_id"],
                    incident["severity"],
                    incident["confidence"],
                    incident["priority"],
                    assigned_to_id,
                    incident["escalation_level"],
                    incident["incident_status"],
                    incident["mitre_tactic"],
                    incident["event_count"],
                    incident["created_at"],
                    incident["updated_at"],
                    incident.get("closed_at"),
                ),
            )

            enrichment = alert["enrichment"]
            connection.execute(
                """
                INSERT INTO enrichment (
                    incident_id,
                    ip_reputation,
                    geo_location,
                    user_typical_location,
                    asset_criticality,
                    account_type,
                    repeat_alert_count,
                    notes,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    incident["incident_id"],
                    enrichment["ip_reputation"],
                    enrichment["geo_location"],
                    enrichment["user_typical_location"],
                    enrichment["asset_criticality"],
                    enrichment["account_type"],
                    enrichment["repeat_alert_count"],
                    enrichment["notes"],
                    enrichment.get("created_at", incident["created_at"]),
                ),
            )

            for note in alert.get("notes", []):
                connection.execute(
                    """
                    INSERT INTO notes (
                        incident_id,
                        author_user_id,
                        note_type,
                        content,
                        visible_to_reporter,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        incident["incident_id"],
                        user_lookup[note["author_username"]],
                        note["note_type"],
                        note["content"],
                        int(note.get("visible_to_reporter", False)),
                        note["created_at"],
                    ),
                )

            connection.execute(
                """
                INSERT INTO audit_log (user_id, incident_id, action, details, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    assigned_to_id or reporter_id,
                    incident["incident_id"],
                    "seed_incident",
                    f"Seeded {alert['alert_type']} sample incident.",
                    incident["created_at"],
                ),
            )

        connection.commit()

        return {
            "users": connection.execute("SELECT COUNT(*) AS total FROM users").fetchone()["total"],
            "alerts": connection.execute("SELECT COUNT(*) AS total FROM alerts").fetchone()["total"],
            "incidents": connection.execute("SELECT COUNT(*) AS total FROM incidents").fetchone()["total"],
            "playbooks": connection.execute("SELECT COUNT(*) AS total FROM playbooks").fetchone()["total"],
        }


def bootstrap_demo_data() -> dict[str, int]:
    """Ensure the schema and demo rows exist before app use."""
    init_db()
    with get_connection() as connection:
        total = connection.execute("SELECT COUNT(*) AS total FROM users").fetchone()["total"]
    if total == 0:
        return seed_demo_data(reset=False)
    return seed_demo_data(reset=False)

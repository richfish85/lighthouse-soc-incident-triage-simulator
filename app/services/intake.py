"""Alert intake services for Lighthouse SOC."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from app.auth import ensure_permission
from app.database import get_connection
from app.roles import Permission
from app.services import incidents


ALERT_TYPES = (
    "Phishing Reported",
    "Impossible Travel Login",
    "Repeated Failed Logins",
    "Malware Detection",
    "Suspicious PowerShell",
    "Privilege Escalation Attempt",
)


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _next_alert_id(connection) -> str:
    row = connection.execute(
        """
        SELECT alert_id
        FROM alerts
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()
    if not row:
        return "ALT-1001"
    current = int(str(row["alert_id"]).split("-")[1])
    return f"ALT-{current + 1:04d}"


def list_alert_types() -> tuple[str, ...]:
    return ALERT_TYPES


def _normalize_text(value: object, fallback: str = "") -> str:
    text = str(value or "").strip()
    return text if text else fallback


def _normalize_attachments(attachments: list[dict[str, object]] | None) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    for attachment in attachments or []:
        name = _normalize_text(attachment.get("name"), "")
        if not name:
            continue
        normalized.append(
            {
                "name": name,
                "size": int(attachment.get("size") or 0),
                "type": _normalize_text(attachment.get("type"), "application/octet-stream"),
            }
        )
    return normalized


def _resolve_evidence_name(payload: dict[str, Any], attachments: list[dict[str, object]]) -> str:
    evidence_name = _normalize_text(payload.get("evidence_name"), "")
    if evidence_name:
        return evidence_name
    if attachments:
        return str(attachments[0]["name"])
    return "metadata_only_submission"


def _deserialize_alert_record(row) -> dict[str, Any]:
    alert = dict(row)
    alert["attachments"] = json.loads(alert.pop("attachments_json", "[]") or "[]")
    alert["attachment_count"] = len(alert["attachments"])
    return alert


def create_alert(user: dict[str, object], payload: dict[str, Any]) -> dict[str, Any]:
    """Create a reporter-submitted alert and auto-open an incident."""
    ensure_permission(user, Permission.SUBMIT_ALERT)
    timestamp = _utc_now()
    attachments = _normalize_attachments(payload.get("attachments"))
    evidence_name = _resolve_evidence_name(payload, attachments)
    contact_info = _normalize_text(payload.get("contact_info"), str(user["email"]))
    affected_user = _normalize_text(payload.get("affected_user"), "Unknown user")
    affected_asset = _normalize_text(payload.get("affected_asset"), "Unknown asset")
    source_ip = _normalize_text(payload.get("source_ip"), "Unknown")
    location = _normalize_text(payload.get("location"), "")
    occurred_at = _normalize_text(payload.get("occurred_at"), "")

    with get_connection() as connection:
        alert_id = _next_alert_id(connection)
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'New', ?, ?)
            """,
            (
                alert_id,
                user["id"],
                payload["alert_type"],
                payload["severity_estimate"],
                _normalize_text(payload.get("description"), "No description provided."),
                affected_user,
                affected_asset,
                source_ip,
                evidence_name,
                occurred_at or None,
                location or None,
                json.dumps(attachments),
                contact_info,
                json.dumps(payload.get("raw_payload", {"provider": "Manual Report", "event_type": "ManualAlert"})),
                timestamp,
                timestamp,
            ),
        )
        connection.commit()
        incidents.open_incident(alert_id, actor_user=None, connection=connection)
        connection.commit()

    return get_alert(alert_id, user)


def list_reporter_alerts(user: dict[str, object]) -> list[dict[str, Any]]:
    """Return alerts created by the signed-in reporter."""
    ensure_permission(user, Permission.VIEW_OWN_ALERTS)
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                a.id,
                a.alert_id,
                a.alert_type,
                a.severity_estimate,
                a.description,
                a.affected_user,
                a.affected_asset,
                a.source_ip,
                a.evidence_name,
                a.occurred_at,
                a.location,
                a.attachments_json,
                a.contact_info,
                a.status,
                a.created_at,
                a.updated_at,
                i.incident_id,
                i.priority,
                i.confidence,
                i.incident_status,
                assignee.username AS assigned_to_username,
                assignee.full_name AS assigned_to_name
            FROM alerts a
            LEFT JOIN incidents i ON i.alert_id = a.alert_id
            LEFT JOIN users assignee ON assignee.id = i.assigned_to
            WHERE a.reporter_user_id = ?
            ORDER BY a.created_at DESC
            """,
            (user["id"],),
        ).fetchall()
    return [_deserialize_alert_record(row) for row in rows]


def get_alert(alert_id: str, viewer: dict[str, object]) -> dict[str, Any]:
    """Return one alert, limiting reporter visibility to their own records."""
    query = """
        SELECT
            a.id,
            a.alert_id,
            a.alert_type,
            a.severity_estimate,
            a.description,
            a.affected_user,
            a.affected_asset,
            a.source_ip,
            a.evidence_name,
            a.occurred_at,
            a.location,
            a.attachments_json,
            a.contact_info,
            a.raw_payload,
            a.status,
            a.created_at,
            a.updated_at,
            i.incident_id,
            i.priority,
            i.confidence,
            i.incident_status,
            i.severity,
            assignee.username AS assigned_to_username,
            assignee.full_name AS assigned_to_name
        FROM alerts a
        LEFT JOIN incidents i ON i.alert_id = a.alert_id
        LEFT JOIN users assignee ON assignee.id = i.assigned_to
        WHERE a.alert_id = ?
    """
    values: list[object] = [alert_id]

    if str(viewer["role"]) == "Reporter":
        query += " AND a.reporter_user_id = ?"
        values.append(viewer["id"])

    with get_connection() as connection:
        row = connection.execute(query, values).fetchone()
        if not row:
            raise LookupError(f"Alert {alert_id} was not found.")
        alert = _deserialize_alert_record(row)
        alert["raw_payload"] = json.loads(alert["raw_payload"])

        notes_query = """
            SELECT
                n.id,
                n.note_type,
                n.content,
                n.visible_to_reporter,
                n.created_at,
                u.full_name AS author_name
            FROM notes n
            JOIN users u ON u.id = n.author_user_id
            WHERE n.incident_id = ?
        """
        note_values: list[object] = [alert["incident_id"]]
        if str(viewer["role"]) == "Reporter":
            notes_query += " AND n.visible_to_reporter = 1"
        notes_query += " ORDER BY n.created_at ASC"
        notes = connection.execute(notes_query, note_values).fetchall()

    alert["notes"] = [dict(note) for note in notes]
    return alert

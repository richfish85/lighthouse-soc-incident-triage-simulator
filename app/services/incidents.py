"""Incident lifecycle services for Lighthouse SOC."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from app.auth import ensure_permission, get_user_by_username
from app.database import get_connection
from app.roles import Permission
from app.services.enrichment import build_enrichment, store_enrichment
from app.services.playbooks import get_playbook
from app.services.scoring import derive_confidence, normalize_severity, score_incident


INCIDENT_STATUSES = (
    "New",
    "In Review",
    "Escalated",
    "Contained",
    "Closed",
    "False Positive",
)

CLOSED_STATUSES = {"Closed", "False Positive"}

MITRE_TACTICS = {
    "Phishing Reported": "Initial Access",
    "Impossible Travel Login": "Credential Access",
    "Repeated Failed Logins": "Credential Access",
    "Malware Detection": "Execution",
    "Suspicious PowerShell": "Execution",
    "Privilege Escalation Attempt": "Privilege Escalation",
}


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _age_label(created_at: str) -> str:
    started = datetime.fromisoformat(created_at)
    delta = datetime.now(UTC) - started.replace(tzinfo=UTC) if started.tzinfo is None else datetime.now(UTC) - started
    minutes = int(delta.total_seconds() // 60)
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h"
    days = hours // 24
    return f"{days}d"


def _next_incident_id(connection) -> str:
    row = connection.execute(
        """
        SELECT incident_id
        FROM incidents
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()
    if not row:
        return "INC-2001"
    current = int(str(row["incident_id"]).split("-")[1])
    return f"INC-{current + 1:04d}"


def _write_audit(connection, user_id: int | None, incident_id: str, action: str, details: str) -> None:
    connection.execute(
        """
        INSERT INTO audit_log (user_id, incident_id, action, details, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, incident_id, action, details, _utc_now()),
    )


def _incident_row_to_payload(row) -> dict[str, Any]:
    payload = dict(row)
    payload["age"] = _age_label(payload["created_at"])
    payload["reporter_name"] = payload.pop("reporter_full_name")
    payload["assignee_name"] = payload.pop("assignee_full_name")
    return payload


def _base_incident_query() -> str:
    return """
        SELECT
            i.id,
            i.incident_id,
            i.alert_id,
            i.severity,
            i.confidence,
            i.priority,
            i.escalation_level,
            i.incident_status,
            i.mitre_tactic,
            i.event_count,
            i.created_at,
            i.updated_at,
            i.closed_at,
            a.alert_type,
            a.description,
            a.affected_user,
            a.affected_asset,
            a.source_ip,
            a.status AS alert_status,
            reporter.username AS reporter_username,
            reporter.full_name AS reporter_full_name,
            assignee.username AS assignee_username,
            assignee.full_name AS assignee_full_name,
            e.ip_reputation,
            e.geo_location,
            e.user_typical_location,
            e.asset_criticality,
            e.account_type,
            e.repeat_alert_count,
            e.notes AS enrichment_notes
        FROM incidents i
        JOIN alerts a ON a.alert_id = i.alert_id
        JOIN users reporter ON reporter.id = a.reporter_user_id
        LEFT JOIN users assignee ON assignee.id = i.assigned_to
        LEFT JOIN enrichment e ON e.incident_id = i.incident_id
    """


def open_incident(
    alert_id: str,
    actor_user: dict[str, object] | None = None,
    connection=None,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create an incident from an alert if one does not already exist."""
    overrides = overrides or {}
    owns_connection = connection is None
    connection = connection or get_connection()

    existing = connection.execute(
        f"{_base_incident_query()} WHERE i.alert_id = ?",
        (alert_id,),
    ).fetchone()
    if existing:
        payload = _incident_row_to_payload(existing)
        if owns_connection:
            connection.close()
        return payload

    alert = connection.execute(
        """
        SELECT a.*, reporter.username AS reporter_username
        FROM alerts a
        JOIN users reporter ON reporter.id = a.reporter_user_id
        WHERE a.alert_id = ?
        """,
        (alert_id,),
    ).fetchone()
    if not alert:
        raise LookupError(f"Alert {alert_id} was not found.")

    alert_payload = dict(alert)
    raw_payload = alert_payload.get("raw_payload")
    if isinstance(raw_payload, str):
        alert_payload["raw_payload"] = json.loads(raw_payload)
    enrichment = build_enrichment(alert_payload)
    created_at = overrides.get("created_at", _utc_now())
    incident_id = overrides.get("incident_id", _next_incident_id(connection))
    severity = normalize_severity(overrides.get("severity", alert_payload["severity_estimate"]))
    confidence = overrides.get(
        "confidence",
        derive_confidence(enrichment["ip_reputation"], enrichment["repeat_alert_count"]),
    )
    scoring = score_incident(
        severity,
        confidence,
        enrichment["asset_criticality"],
        enrichment["account_type"],
    )
    incident_status = overrides.get("incident_status", "New")
    if incident_status not in INCIDENT_STATUSES:
        raise ValueError(f"Unsupported incident status: {incident_status}")

    assignee_username = overrides.get("assigned_to")
    assignee = get_user_by_username(assignee_username) if assignee_username else None

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
            incident_id,
            alert_id,
            scoring["severity"],
            scoring["confidence"],
            overrides.get("priority", scoring["priority"]),
            assignee["id"] if assignee else None,
            int(overrides.get("escalation_level", 0)),
            incident_status,
            overrides.get("mitre_tactic", MITRE_TACTICS.get(alert_payload["alert_type"], "Discovery")),
            int(overrides.get("event_count", alert_payload.get("raw_payload", {}).get("event_count", 1))),
            created_at,
            overrides.get("updated_at", created_at),
            overrides.get("closed_at"),
        ),
    )

    store_enrichment(incident_id, overrides.get("enrichment", enrichment), created_at, connection=connection)
    _write_audit(
        connection,
        int(actor_user["id"]) if actor_user else None,
        incident_id,
        "incident_opened",
        f"Incident created from alert {alert_id}.",
    )

    row = connection.execute(
        f"{_base_incident_query()} WHERE i.incident_id = ?",
        (incident_id,),
    ).fetchone()
    payload = _incident_row_to_payload(row)
    payload["notes"] = []
    payload["playbook"] = get_playbook(payload["alert_type"], {"role": "Admin"})

    if owns_connection:
        connection.commit()
        connection.close()

    return payload


def list_incidents(
    viewer: dict[str, object],
    filters: dict[str, object] | None = None,
) -> list[dict[str, Any]]:
    """Return incidents visible to analysts and admins."""
    ensure_permission(viewer, Permission.VIEW_ALL_INCIDENTS)
    filters = filters or {}

    clauses: list[str] = []
    values: list[object] = []

    if filters.get("severity"):
        clauses.append("i.severity = ?")
        values.append(filters["severity"])
    if filters.get("status"):
        clauses.append("i.incident_status = ?")
        values.append(filters["status"])
    if filters.get("priority"):
        clauses.append("i.priority = ?")
        values.append(filters["priority"])
    if filters.get("assigned_to_me"):
        clauses.append("assignee.username = ?")
        values.append(viewer["username"])
    if filters.get("assignee_username"):
        clauses.append("assignee.username = ?")
        values.append(filters["assignee_username"])

    query = _base_incident_query()
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY i.priority ASC, i.updated_at DESC"

    with get_connection() as connection:
        rows = connection.execute(query, values).fetchall()

    return [_incident_row_to_payload(row) for row in rows]


def get_incident(incident_id: str, viewer: dict[str, object]) -> dict[str, Any]:
    """Return one incident with enrichment, notes, and playbook data."""
    ensure_permission(viewer, Permission.VIEW_ALL_INCIDENTS)
    with get_connection() as connection:
        row = connection.execute(
            f"{_base_incident_query()} WHERE i.incident_id = ?",
            (incident_id,),
        ).fetchone()
        if not row:
            raise LookupError(f"Incident {incident_id} was not found.")

        incident = _incident_row_to_payload(row)
        notes = connection.execute(
            """
            SELECT
                n.id,
                n.incident_id,
                n.note_type,
                n.content,
                n.visible_to_reporter,
                n.created_at,
                u.username AS author_username,
                u.full_name AS author_full_name
            FROM notes n
            JOIN users u ON u.id = n.author_user_id
            WHERE n.incident_id = ?
            ORDER BY n.created_at ASC
            """,
            (incident_id,),
        ).fetchall()

    incident["notes"] = [dict(note) for note in notes]
    incident["playbook"] = get_playbook(incident["alert_type"], viewer)
    return incident


def assign_incident(incident_id: str, assignee_username: str, actor_user: dict[str, object]) -> dict[str, Any]:
    """Assign an incident to a named analyst user."""
    ensure_permission(actor_user, Permission.UPDATE_INCIDENT)
    assignee = get_user_by_username(assignee_username)
    timestamp = _utc_now()

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE incidents
            SET assigned_to = ?, updated_at = ?
            WHERE incident_id = ?
            """,
            (assignee["id"], timestamp, incident_id),
        )
        _write_audit(
            connection,
            int(actor_user["id"]),
            incident_id,
            "incident_assigned",
            f"Assigned to {assignee_username}.",
        )
        connection.commit()

    return get_incident(incident_id, actor_user)


def update_status(incident_id: str, new_status: str, actor_user: dict[str, object]) -> dict[str, Any]:
    """Update the incident and linked alert lifecycle state."""
    ensure_permission(actor_user, Permission.UPDATE_INCIDENT)
    status = new_status.strip().title()
    if status not in INCIDENT_STATUSES:
        raise ValueError(f"Unsupported incident status: {new_status}")

    timestamp = _utc_now()
    closed_at = timestamp if status in CLOSED_STATUSES else None

    with get_connection() as connection:
        alert_row = connection.execute(
            "SELECT alert_id FROM incidents WHERE incident_id = ?",
            (incident_id,),
        ).fetchone()
        if not alert_row:
            raise LookupError(f"Incident {incident_id} was not found.")

        connection.execute(
            """
            UPDATE incidents
            SET incident_status = ?, updated_at = ?, closed_at = ?
            WHERE incident_id = ?
            """,
            (status, timestamp, closed_at, incident_id),
        )
        connection.execute(
            """
            UPDATE alerts
            SET status = ?, updated_at = ?
            WHERE alert_id = ?
            """,
            (status, timestamp, alert_row["alert_id"]),
        )
        _write_audit(
            connection,
            int(actor_user["id"]),
            incident_id,
            "status_updated",
            f"Updated incident to {status}.",
        )
        connection.commit()

    return get_incident(incident_id, actor_user)


def add_note(
    incident_id: str,
    actor_user: dict[str, object],
    content: str,
    note_type: str = "analyst_note",
    visible_to_reporter: bool = False,
) -> dict[str, Any]:
    """Attach an investigation note to an incident."""
    ensure_permission(actor_user, Permission.ADD_NOTES)
    note = content.strip()
    if not note:
        raise ValueError("Note content cannot be empty.")

    timestamp = _utc_now()
    with get_connection() as connection:
        cursor = connection.execute(
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
            (incident_id, actor_user["id"], note_type, note, int(visible_to_reporter), timestamp),
        )
        note_id = cursor.lastrowid
        connection.execute(
            """
            UPDATE incidents
            SET updated_at = ?
            WHERE incident_id = ?
            """,
            (timestamp, incident_id),
        )
        _write_audit(connection, int(actor_user["id"]), incident_id, "note_added", note_type)
        connection.commit()

        row = connection.execute(
            """
            SELECT
                n.id,
                n.incident_id,
                n.note_type,
                n.content,
                n.visible_to_reporter,
                n.created_at,
                u.username AS author_username,
                u.full_name AS author_full_name
            FROM notes n
            JOIN users u ON u.id = n.author_user_id
            WHERE n.id = ?
            """
            ,
            (note_id,),
        ).fetchone()

    return dict(row)


def escalate_incident(incident_id: str, actor_user: dict[str, object], reason: str = "") -> dict[str, Any]:
    """Escalate an incident and optionally record a note."""
    ensure_permission(actor_user, Permission.ESCALATE_INCIDENT)
    timestamp = _utc_now()
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT escalation_level, alert_id
            FROM incidents
            WHERE incident_id = ?
            """,
            (incident_id,),
        ).fetchone()
        if not row:
            raise LookupError(f"Incident {incident_id} was not found.")

        next_level = int(row["escalation_level"]) + 1
        connection.execute(
            """
            UPDATE incidents
            SET escalation_level = ?, incident_status = 'Escalated', updated_at = ?
            WHERE incident_id = ?
            """,
            (next_level, timestamp, incident_id),
        )
        connection.execute(
            """
            UPDATE alerts
            SET status = 'Escalated', updated_at = ?
            WHERE alert_id = ?
            """,
            (timestamp, row["alert_id"]),
        )

        if reason.strip():
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
                VALUES (?, ?, 'escalation_note', ?, 0, ?)
                """,
                (incident_id, actor_user["id"], reason.strip(), timestamp),
            )

        _write_audit(
            connection,
            int(actor_user["id"]),
            incident_id,
            "incident_escalated",
            f"Escalation level raised to {next_level}.",
        )
        connection.commit()

    return get_incident(incident_id, actor_user)

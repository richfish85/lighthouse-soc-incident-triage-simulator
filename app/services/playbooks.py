"""Playbook retrieval helpers for Lighthouse SOC."""

from __future__ import annotations

import json

from app.auth import ensure_permission
from app.database import get_connection
from app.roles import Permission


def list_playbooks(viewer: dict[str, object] | None = None) -> list[dict[str, object]]:
    """Return all playbooks in alert-type order."""
    if viewer is not None:
        ensure_permission(viewer, Permission.VIEW_PLAYBOOKS)

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, alert_type, title, steps_json, severity_hint, created_at
            FROM playbooks
            ORDER BY alert_type
            """
        ).fetchall()

    playbooks: list[dict[str, object]] = []
    for row in rows:
        payload = dict(row)
        payload["steps"] = json.loads(payload.pop("steps_json"))
        playbooks.append(payload)
    return playbooks


def get_playbook(alert_type: str, viewer: dict[str, object] | None = None) -> dict[str, object]:
    """Fetch a single playbook for a given alert type."""
    if viewer is not None:
        ensure_permission(viewer, Permission.VIEW_PLAYBOOKS)

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, alert_type, title, steps_json, severity_hint, created_at
            FROM playbooks
            WHERE alert_type = ?
            """,
            (alert_type,),
        ).fetchone()

    if not row:
        raise LookupError(f"No playbook found for alert type: {alert_type}")

    payload = dict(row)
    payload["steps"] = json.loads(payload.pop("steps_json"))
    return payload

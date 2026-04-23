"""Metrics helpers for the Lighthouse SOC admin dashboard."""

from __future__ import annotations

from datetime import datetime

from app.auth import ensure_permission
from app.database import get_connection
from app.roles import Permission


def _minutes_between(start_value: str, end_value: str) -> float:
    start = datetime.fromisoformat(start_value)
    end = datetime.fromisoformat(end_value)
    return round((end - start).total_seconds() / 60, 1)


def get_dashboard_metrics(viewer: dict[str, object]) -> dict[str, object]:
    """Return headline metrics and chart-ready data."""
    ensure_permission(viewer, Permission.VIEW_ANALYTICS)

    with get_connection() as connection:
        total_alerts = connection.execute("SELECT COUNT(*) AS total FROM alerts").fetchone()["total"]
        total_incidents = connection.execute("SELECT COUNT(*) AS total FROM incidents").fetchone()["total"]
        open_incidents = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM incidents
            WHERE incident_status NOT IN ('Closed', 'False Positive')
            """
        ).fetchone()["total"]
        critical_incidents = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM incidents
            WHERE priority IN ('P1', 'P2')
            """
        ).fetchone()["total"]
        escalations = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM incidents
            WHERE escalation_level > 0 OR incident_status = 'Escalated'
            """
        ).fetchone()["total"]
        false_positives = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM incidents
            WHERE incident_status = 'False Positive'
            """
        ).fetchone()["total"]

        triage_rows = connection.execute(
            """
            SELECT created_at, updated_at
            FROM incidents
            """
        ).fetchall()
        mean_triage_time = 0.0
        if triage_rows:
            durations = [_minutes_between(row["created_at"], row["updated_at"]) for row in triage_rows]
            mean_triage_time = round(sum(durations) / len(durations), 1)

        severity_rows = connection.execute(
            """
            SELECT severity, COUNT(*) AS count
            FROM incidents
            GROUP BY severity
            ORDER BY count DESC, severity ASC
            """
        ).fetchall()
        trend_rows = connection.execute(
            """
            SELECT substr(created_at, 1, 10) AS day, COUNT(*) AS count
            FROM alerts
            GROUP BY day
            ORDER BY day ASC
            """
        ).fetchall()
        alert_type_rows = connection.execute(
            """
            SELECT alert_type, COUNT(*) AS count
            FROM alerts
            GROUP BY alert_type
            ORDER BY count DESC, alert_type ASC
            """
        ).fetchall()
        status_rows = connection.execute(
            """
            SELECT incident_status AS status, COUNT(*) AS count
            FROM incidents
            GROUP BY incident_status
            ORDER BY count DESC, incident_status ASC
            """
        ).fetchall()

    false_positive_rate = round((false_positives / total_incidents) * 100, 1) if total_incidents else 0.0

    return {
        "totals": {
            "total_alerts": total_alerts,
            "total_incidents": total_incidents,
            "open_incidents": open_incidents,
            "critical_incidents": critical_incidents,
            "escalations": escalations,
            "mean_triage_minutes": mean_triage_time,
            "false_positive_rate": false_positive_rate,
        },
        "alerts_by_severity": [dict(row) for row in severity_rows],
        "alert_trends": [dict(row) for row in trend_rows],
        "top_alert_types": [dict(row) for row in alert_type_rows],
        "status_breakdown": [dict(row) for row in status_rows],
    }

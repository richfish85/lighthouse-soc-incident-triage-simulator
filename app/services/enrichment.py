"""Alert enrichment helpers backed by sample asset and reputation data."""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Mapping

from app.database import get_connection
from app.seed import load_json_file


@lru_cache(maxsize=1)
def _asset_index() -> dict[str, dict[str, Any]]:
    assets = load_json_file("sample_assets.json")
    return {asset["asset_name"]: asset for asset in assets}


@lru_cache(maxsize=1)
def _ip_index() -> dict[str, dict[str, Any]]:
    reputations = load_json_file("sample_ip_reputation.json")
    return {item["source_ip"]: item for item in reputations}


@lru_cache(maxsize=1)
def _identity_index() -> dict[str, dict[str, Any]]:
    users = load_json_file("sample_users.json")
    return {profile["username"]: profile for profile in users["identity_profiles"]}


def build_enrichment(alert: Mapping[str, Any]) -> dict[str, Any]:
    """Create enrichment context from static demo data plus prior alert counts."""
    asset = _asset_index().get(
        str(alert["affected_asset"]),
        {"asset_criticality": "Medium", "asset_owner": str(alert["affected_user"]), "environment": "Corporate"},
    )
    ip_record = _ip_index().get(
        str(alert["source_ip"]),
        {"reputation": "Unknown", "geo_location": "Unknown", "note": "No reputation record found."},
    )
    identity = _identity_index().get(
        str(alert["affected_user"]),
        {"typical_location": "Unknown", "account_type": "Standard"},
    )

    with get_connection() as connection:
        repeat_alert_count = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM alerts
            WHERE (affected_user = ? OR affected_asset = ?)
              AND alert_id != COALESCE(?, '')
            """,
            (
                str(alert["affected_user"]),
                str(alert["affected_asset"]),
                alert.get("alert_id"),
            ),
        ).fetchone()["total"]

    return {
        "ip_reputation": ip_record["reputation"],
        "geo_location": ip_record["geo_location"],
        "user_typical_location": identity["typical_location"],
        "asset_criticality": asset["asset_criticality"],
        "account_type": identity["account_type"],
        "repeat_alert_count": int(repeat_alert_count),
        "notes": (
            f"{ip_record['note']} Asset criticality is {asset['asset_criticality']} "
            f"for {asset.get('environment', 'core')} systems."
        ),
    }


def store_enrichment(
    incident_id: str,
    enrichment: Mapping[str, Any],
    created_at: str,
    connection=None,
) -> None:
    """Insert or update enrichment context for an incident."""
    owns_connection = connection is None
    connection = connection or get_connection()
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
        ON CONFLICT(incident_id) DO UPDATE SET
            ip_reputation = excluded.ip_reputation,
            geo_location = excluded.geo_location,
            user_typical_location = excluded.user_typical_location,
            asset_criticality = excluded.asset_criticality,
            account_type = excluded.account_type,
            repeat_alert_count = excluded.repeat_alert_count,
            notes = excluded.notes
        """,
        (
            incident_id,
            enrichment["ip_reputation"],
            enrichment["geo_location"],
            enrichment["user_typical_location"],
            enrichment["asset_criticality"],
            enrichment["account_type"],
            enrichment["repeat_alert_count"],
            enrichment["notes"],
            created_at,
        ),
    )
    if owns_connection:
        connection.commit()
        connection.close()


def get_enrichment(incident_id: str) -> dict[str, Any]:
    """Return a stored enrichment record."""
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, incident_id, ip_reputation, geo_location, user_typical_location,
                   asset_criticality, account_type, repeat_alert_count, notes, created_at
            FROM enrichment
            WHERE incident_id = ?
            """,
            (incident_id,),
        ).fetchone()
    if not row:
        raise LookupError(f"No enrichment found for incident {incident_id}.")
    return dict(row)

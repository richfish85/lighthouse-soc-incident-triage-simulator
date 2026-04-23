"""Database helpers and schema management for Lighthouse SOC."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT_DIR / "db" / "lighthouse.db"


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL,
    email TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id TEXT NOT NULL UNIQUE,
    reporter_user_id INTEGER NOT NULL,
    alert_type TEXT NOT NULL,
    severity_estimate TEXT NOT NULL,
    description TEXT NOT NULL,
    affected_user TEXT NOT NULL,
    affected_asset TEXT NOT NULL,
    source_ip TEXT NOT NULL,
    evidence_name TEXT NOT NULL,
    occurred_at TEXT,
    location TEXT,
    attachments_json TEXT NOT NULL DEFAULT '[]',
    contact_info TEXT NOT NULL,
    raw_payload TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (reporter_user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id TEXT NOT NULL UNIQUE,
    alert_id TEXT NOT NULL UNIQUE,
    severity TEXT NOT NULL,
    confidence TEXT NOT NULL,
    priority TEXT NOT NULL,
    assigned_to INTEGER,
    escalation_level INTEGER NOT NULL DEFAULT 0,
    incident_status TEXT NOT NULL,
    mitre_tactic TEXT NOT NULL,
    event_count INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    closed_at TEXT,
    FOREIGN KEY (alert_id) REFERENCES alerts(alert_id),
    FOREIGN KEY (assigned_to) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS enrichment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id TEXT NOT NULL UNIQUE,
    ip_reputation TEXT NOT NULL,
    geo_location TEXT NOT NULL,
    user_typical_location TEXT NOT NULL,
    asset_criticality TEXT NOT NULL,
    account_type TEXT NOT NULL,
    repeat_alert_count INTEGER NOT NULL DEFAULT 0,
    notes TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (incident_id) REFERENCES incidents(incident_id)
);

CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id TEXT NOT NULL,
    author_user_id INTEGER NOT NULL,
    note_type TEXT NOT NULL,
    content TEXT NOT NULL,
    visible_to_reporter INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (incident_id) REFERENCES incidents(incident_id),
    FOREIGN KEY (author_user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS playbooks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    steps_json TEXT NOT NULL,
    severity_hint TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    incident_id TEXT,
    action TEXT NOT NULL,
    details TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (incident_id) REFERENCES incidents(incident_id)
);
"""


ALERT_COLUMN_MIGRATIONS: dict[str, str] = {
    "occurred_at": "ALTER TABLE alerts ADD COLUMN occurred_at TEXT",
    "location": "ALTER TABLE alerts ADD COLUMN location TEXT",
    "attachments_json": "ALTER TABLE alerts ADD COLUMN attachments_json TEXT NOT NULL DEFAULT '[]'",
}


def get_db_path() -> Path:
    """Resolve the active database path from the environment or default."""
    configured = os.getenv("LIGHTHOUSE_DB_PATH")
    if configured:
        return Path(configured).expanduser().resolve()
    return DEFAULT_DB_PATH


def get_connection() -> sqlite3.Connection:
    """Open a SQLite connection with dictionary-like rows."""
    path = get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def _ensure_alert_columns(connection: sqlite3.Connection) -> None:
    """Add newly introduced alert columns when opening an older database."""
    existing_columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(alerts)").fetchall()
    }
    for column_name, ddl in ALERT_COLUMN_MIGRATIONS.items():
        if column_name not in existing_columns:
            connection.execute(ddl)


def init_db() -> Path:
    """Create tables when they do not yet exist."""
    path = get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as connection:
        connection.executescript(SCHEMA_SQL)
        _ensure_alert_columns(connection)
        connection.commit()
    return path


def reset_db() -> Path:
    """Reset the database by deleting the file and recreating the schema."""
    path = get_db_path()
    if path.exists():
        path.unlink()
    return init_db()

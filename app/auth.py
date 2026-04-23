"""Seeded user authentication helpers for Lighthouse SOC."""

from __future__ import annotations

from app.database import get_connection, init_db
from app.roles import Permission, require_permission


def list_demo_users() -> list[dict[str, object]]:
    """Return active users in demo login order."""
    init_db()
    query = """
    SELECT id, username, full_name, role, email, is_active, created_at
    FROM users
    WHERE is_active = 1
    ORDER BY CASE role
        WHEN 'Reporter' THEN 1
        WHEN 'Analyst' THEN 2
        WHEN 'Admin' THEN 3
        ELSE 4
    END, username
    """
    with get_connection() as connection:
        rows = connection.execute(query).fetchall()
    return [dict(row) for row in rows]


def get_user_by_username(username: str) -> dict[str, object]:
    """Look up a seeded demo user by username."""
    init_db()
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, username, full_name, role, email, is_active, created_at
            FROM users
            WHERE username = ?
            """,
            (username,),
        ).fetchone()
    if not row:
        raise LookupError(f"Unknown demo user: {username}")
    user = dict(row)
    if not user["is_active"]:
        raise PermissionError(f"User {username} is inactive.")
    return user


def login_demo_user(username: str) -> dict[str, object]:
    """Return a valid active demo user for the requested login."""
    return get_user_by_username(username)


def ensure_permission(user: dict[str, object], permission: Permission) -> None:
    """Thin wrapper around shared RBAC checks."""
    require_permission(user, permission)

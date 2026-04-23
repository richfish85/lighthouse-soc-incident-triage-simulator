"""Role and permission definitions for Lighthouse SOC."""

from __future__ import annotations

from enum import Enum
from typing import Iterable


class Role(str, Enum):
    REPORTER = "Reporter"
    ANALYST = "Analyst"
    ADMIN = "Admin"


class Permission(str, Enum):
    SUBMIT_ALERT = "submit_alert"
    VIEW_OWN_ALERTS = "view_own_alerts"
    VIEW_ALL_INCIDENTS = "view_all_incidents"
    UPDATE_INCIDENT = "update_incident"
    ADD_NOTES = "add_notes"
    ESCALATE_INCIDENT = "escalate_incident"
    VIEW_ANALYTICS = "view_analytics"
    MANAGE_USERS = "manage_users"
    EDIT_PLAYBOOKS = "edit_playbooks"
    EXPORT_REPORTS = "export_reports"
    VIEW_PLAYBOOKS = "view_playbooks"


ROLE_ORDER: tuple[str, ...] = (
    Role.REPORTER.value,
    Role.ANALYST.value,
    Role.ADMIN.value,
)

ROLE_PERMISSIONS: dict[str, set[Permission]] = {
    Role.REPORTER.value: {
        Permission.SUBMIT_ALERT,
        Permission.VIEW_OWN_ALERTS,
    },
    Role.ANALYST.value: {
        Permission.SUBMIT_ALERT,
        Permission.VIEW_OWN_ALERTS,
        Permission.VIEW_ALL_INCIDENTS,
        Permission.UPDATE_INCIDENT,
        Permission.ADD_NOTES,
        Permission.ESCALATE_INCIDENT,
        Permission.VIEW_ANALYTICS,
        Permission.EXPORT_REPORTS,
        Permission.VIEW_PLAYBOOKS,
    },
    Role.ADMIN.value: set(Permission),
}


def normalize_role(role: str) -> str:
    """Return a valid role string or raise a helpful error."""
    cleaned = (role or "").strip().title()
    if cleaned not in ROLE_ORDER:
        raise ValueError(f"Unsupported role: {role!r}")
    return cleaned


def has_permission(role_or_user: str | dict[str, object], permission: Permission) -> bool:
    """Check whether a role or user grants a permission."""
    role = role_or_user["role"] if isinstance(role_or_user, dict) else role_or_user
    return permission in ROLE_PERMISSIONS.get(normalize_role(str(role)), set())


def require_permission(role_or_user: str | dict[str, object], permission: Permission) -> None:
    """Raise when a role or user does not have the required permission."""
    if not has_permission(role_or_user, permission):
        role = role_or_user["role"] if isinstance(role_or_user, dict) else role_or_user
        raise PermissionError(f"Role {role!r} does not have permission {permission.value!r}.")


def role_choices() -> Iterable[str]:
    """Return roles in their preferred demo order."""
    return ROLE_ORDER

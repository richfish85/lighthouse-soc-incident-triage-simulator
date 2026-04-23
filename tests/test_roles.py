from __future__ import annotations

import pytest

from app.roles import Permission, has_permission
from app.services.incidents import update_status


def test_permission_matrix_matches_expected_roles(seeded_db):
    reporter = seeded_db["reporter"]
    analyst = seeded_db["analyst"]
    admin = seeded_db["admin"]

    assert has_permission(reporter, Permission.SUBMIT_ALERT)
    assert not has_permission(reporter, Permission.UPDATE_INCIDENT)

    assert has_permission(analyst, Permission.VIEW_ALL_INCIDENTS)
    assert has_permission(analyst, Permission.ADD_NOTES)
    assert not has_permission(analyst, Permission.MANAGE_USERS)

    assert has_permission(admin, Permission.MANAGE_USERS)
    assert has_permission(admin, Permission.VIEW_ANALYTICS)


def test_reporter_cannot_update_incident_status(seeded_db):
    reporter = seeded_db["reporter"]
    with pytest.raises(PermissionError):
        update_status("INC-2001", "Closed", reporter)

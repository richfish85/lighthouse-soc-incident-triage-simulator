"""Shared dataclasses used across the Lighthouse SOC app."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class User:
    id: int
    username: str
    full_name: str
    role: str
    email: str
    is_active: bool
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Alert:
    id: int
    alert_id: str
    reporter_user_id: int
    alert_type: str
    severity_estimate: str
    description: str
    affected_user: str
    affected_asset: str
    source_ip: str
    evidence_name: str
    occurred_at: str | None
    location: str | None
    attachments_json: str
    contact_info: str
    raw_payload: str
    status: str
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Incident:
    id: int
    incident_id: str
    alert_id: str
    severity: str
    confidence: str
    priority: str
    assigned_to: int | None
    escalation_level: int
    incident_status: str
    mitre_tactic: str
    event_count: int
    created_at: str
    updated_at: str
    closed_at: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Enrichment:
    id: int
    incident_id: str
    ip_reputation: str
    geo_location: str
    user_typical_location: str
    asset_criticality: str
    account_type: str
    repeat_alert_count: int
    notes: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Note:
    id: int
    incident_id: str
    author_user_id: int
    note_type: str
    content: str
    visible_to_reporter: bool
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Playbook:
    id: int
    alert_type: str
    title: str
    steps_json: str
    severity_hint: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AuditLog:
    id: int
    user_id: int | None
    incident_id: str | None
    action: str
    details: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

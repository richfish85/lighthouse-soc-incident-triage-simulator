"""Scoring logic used to prioritize Lighthouse SOC incidents."""

from __future__ import annotations

SEVERITY_WEIGHTS = {
    "Low": 1,
    "Medium": 2,
    "High": 3,
    "Critical": 4,
}

CONFIDENCE_WEIGHTS = {
    "Low": 1,
    "Medium": 2,
    "High": 3,
}

ASSET_CRITICALITY_WEIGHTS = {
    "Low": 1,
    "Medium": 2,
    "High": 3,
    "Critical": 4,
}

ACCOUNT_TYPE_WEIGHTS = {
    "Standard": 0,
    "Privileged": 2,
    "Service": 1,
}


def _normalize_level(value: str, valid_values: dict[str, int], fallback: str) -> str:
    cleaned = (value or "").strip().title()
    return cleaned if cleaned in valid_values else fallback


def normalize_severity(value: str) -> str:
    return _normalize_level(value, SEVERITY_WEIGHTS, "Medium")


def normalize_confidence(value: str) -> str:
    return _normalize_level(value, CONFIDENCE_WEIGHTS, "Medium")


def normalize_asset_criticality(value: str) -> str:
    return _normalize_level(value, ASSET_CRITICALITY_WEIGHTS, "Medium")


def normalize_account_type(value: str) -> str:
    cleaned = (value or "").strip().title()
    return cleaned if cleaned in ACCOUNT_TYPE_WEIGHTS else "Standard"


def derive_confidence(ip_reputation: str, repeat_alert_count: int) -> str:
    """Infer analyst confidence from reputation signals and repeat activity."""
    reputation = (ip_reputation or "").strip().title()
    if reputation == "Malicious" or repeat_alert_count >= 3:
        return "High"
    if reputation == "Suspicious" or repeat_alert_count >= 1:
        return "Medium"
    return "Low"


def calculate_priority_score(
    severity: str,
    confidence: str,
    asset_criticality: str,
    account_type: str,
) -> int:
    """Calculate the numeric score used to place incidents into P1-P5 buckets."""
    return (
        SEVERITY_WEIGHTS[normalize_severity(severity)]
        + CONFIDENCE_WEIGHTS[normalize_confidence(confidence)]
        + ASSET_CRITICALITY_WEIGHTS[normalize_asset_criticality(asset_criticality)]
        + ACCOUNT_TYPE_WEIGHTS[normalize_account_type(account_type)]
    )


def score_incident(
    severity: str,
    confidence: str,
    asset_criticality: str,
    account_type: str,
) -> dict[str, object]:
    """Return a complete scoring payload for a new or updated incident."""
    normalized_severity = normalize_severity(severity)
    normalized_confidence = normalize_confidence(confidence)
    normalized_asset_criticality = normalize_asset_criticality(asset_criticality)
    normalized_account_type = normalize_account_type(account_type)
    score = calculate_priority_score(
        normalized_severity,
        normalized_confidence,
        normalized_asset_criticality,
        normalized_account_type,
    )

    if score >= 11:
        priority = "P1"
    elif score >= 9:
        priority = "P2"
    elif score >= 7:
        priority = "P3"
    elif score >= 5:
        priority = "P4"
    else:
        priority = "P5"

    return {
        "severity": normalized_severity,
        "confidence": normalized_confidence,
        "asset_criticality": normalized_asset_criticality,
        "account_type": normalized_account_type,
        "score": score,
        "priority": priority,
    }

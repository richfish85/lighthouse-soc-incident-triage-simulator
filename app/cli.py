"""Command-line entry point for Lighthouse SOC."""

from __future__ import annotations

import argparse
import json

from app.auth import get_user_by_username
from app.database import init_db
from app.seed import bootstrap_demo_data, seed_demo_data
from app.services.incidents import add_note, escalate_incident, get_incident, update_status
from app.services.intake import create_alert
from app.services.metrics import get_dashboard_metrics


def run_smoke_demo() -> dict[str, object]:
    """Execute the required CLI smoke path against demo data."""
    seed_demo_data(reset=True)
    reporter = get_user_by_username("reporter01")
    analyst = get_user_by_username("analyst01")
    admin = get_user_by_username("admin01")

    created = create_alert(
        reporter,
        {
            "alert_type": "Phishing Reported",
            "severity_estimate": "Medium",
            "description": "User reported a suspicious invoice email with a login lure.",
            "affected_user": "nina.rojas",
            "affected_asset": "MKT-LAPTOP-22",
            "source_ip": "203.0.113.19",
            "evidence_name": "invoice_lure.eml",
            "contact_info": "mia.santos@lighthouse.demo",
            "raw_payload": {"provider": "Manual Report", "event_type": "SmokeTestAlert", "event_count": 1},
        },
    )

    incident = get_incident(created["incident_id"], analyst)
    add_note(
        incident["incident_id"],
        analyst,
        "Smoke test note: validating playbook attachment and queue update.",
    )
    escalate_incident(incident["incident_id"], analyst, "Smoke test escalation to validate workflow.")
    closed = update_status(incident["incident_id"], "Closed", analyst)
    metrics = get_dashboard_metrics(admin)

    return {
        "created_alert_id": created["alert_id"],
        "created_incident_id": incident["incident_id"],
        "final_status": closed["incident_status"],
        "priority": closed["priority"],
        "dashboard_totals": metrics["totals"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Lighthouse SOC CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-db", help="Create the SQLite schema.")

    seed_parser = subparsers.add_parser("seed", help="Seed the demo database.")
    seed_parser.add_argument("--reset", action="store_true", help="Reset the database before seeding.")

    subparsers.add_parser("bootstrap", help="Ensure demo data exists.")
    subparsers.add_parser("smoke", help="Run the incident lifecycle smoke workflow.")

    args = parser.parse_args()

    if args.command == "init-db":
        path = init_db()
        print(f"Database initialised at {path}")
    elif args.command == "seed":
        counts = seed_demo_data(reset=args.reset)
        print(json.dumps(counts, indent=2))
    elif args.command == "bootstrap":
        counts = bootstrap_demo_data()
        print(json.dumps(counts, indent=2))
    elif args.command == "smoke":
        result = run_smoke_demo()
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

# ARCHITECTURE

## What
Lighthouse SOC is a single-application SOC triage simulator with one shared backend, one shared SQLite database, and role-based UI flows.

Core subsystems:

- `Streamlit UI`
- `Service layer`
- `SQLite persistence`
- `JSON-backed demo context`

## Checklist
- [x] One app
- [x] Three roles
- [x] Shared data model
- [x] Thin UI over reusable services

## Why
The architecture is designed for clarity first.

That means:

- the UI can change without rewriting triage logic
- tests can hit services directly
- future API routes can mirror existing service boundaries

Example:

- today `create_alert()` is used by the Streamlit reporter form
- later the same function can back `POST /api/alerts`

## Checklist
- [x] Service-first design
- [x] Future API shape reflected in naming
- [x] Minimal infrastructure overhead

## How
## High-Level Shape
```text
Reporter / Analyst / Admin
          |
      Streamlit
          |
     Service Layer
          |
       SQLite DB
          |
   JSON Sample Context
```

## Core Modules
- `app/database.py`
  Creates the schema and manages SQLite connections.
- `app/seed.py`
  Loads deterministic demo data into the database.
- `app/auth.py`
  Resolves seeded users and supports simple demo login.
- `app/roles.py`
  Defines roles, permissions, and RBAC checks.
- `app/services/intake.py`
  Creates alerts and auto-opens incidents.
- `app/services/enrichment.py`
  Combines IP reputation, asset context, and identity baselines.
- `app/services/scoring.py`
  Converts risk signals into `P1` through `P5`.
- `app/services/incidents.py`
  Owns assignment, notes, escalation, and status changes.
- `app/services/metrics.py`
  Builds dashboard totals and chart-ready aggregations.
- `app/services/playbooks.py`
  Retrieves response guidance by alert type.

## Data Model
- `users`
  Demo application users.
- `alerts`
  Reporter-submitted or ingested alert records.
- `incidents`
  Analyst-owned triage records linked one-to-one with alerts for the MVP.
- `enrichment`
  Context added around an incident.
- `notes`
  Analyst and system notes attached to incidents.
- `playbooks`
  Alert-type response guidance.
- `audit_log`
  Change trace for incident actions.

## Request And Data Flow
### Reporter flow
1. Reporter logs in with a seeded demo user.
2. Reporter submits an alert in Streamlit.
3. `create_alert()` writes the alert to SQLite.
4. `open_incident()` auto-creates an incident.
5. `build_enrichment()` and `score_incident()` add context and priority.

### Analyst flow
1. Analyst loads queue data with filters.
2. Analyst opens an incident.
3. Incident detail joins alert, enrichment, notes, assignee, and playbook data.
4. Analyst assigns, notes, escalates, or updates status.
5. Actions are written to `incidents`, `alerts`, `notes`, and `audit_log`.

### Admin flow
1. Admin loads dashboard metrics.
2. `get_dashboard_metrics()` aggregates counts and chart data.
3. Admin opens oversight to review specific incident details and notes.

## Design Decisions
- `SQLite` instead of an ORM:
  simpler for a small deterministic MVP.
- `Streamlit` instead of a larger web framework:
  faster delivery of a polished demo.
- `JSON` seed context:
  easier to inspect, edit, and present in a portfolio repo.
- `RBAC in services`:
  important because UI page visibility alone is not enough.

## Assumptions
- This is a single-user or low-concurrency demo environment.
- A one-alert-to-one-incident mapping is acceptable for v1.
- Seeded users are enough for demos and tests.

## Validation Hooks
- `python -m app.cli seed --reset`
- `python -m app.cli smoke`
- `streamlit run app/main.py`
- `python -m pytest`

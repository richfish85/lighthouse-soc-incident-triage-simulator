# ROADMAP

## What
This roadmap shows where Lighthouse SOC is today and what should come next.

The current version is an MVP focused on one believable SOC workflow:

- submit an alert
- triage it
- investigate it
- update status
- review admin metrics

## Checklist
- [x] Define MVP scope
- [x] Implement role-based simulator
- [x] Add portfolio-ready docs and diagrams
- [ ] Expand analyst tooling beyond MVP
- [ ] Add stronger auth and reporting later

## Why
The project is intentionally phased.

That helps in two ways:

- the MVP stays clean and explainable
- later enhancements have a clear place to land

Example:

- `Streamlit + SQLite` is right for a demo today
- a future `Flask/FastAPI + real auth` layer can come later if the project grows

## Checklist
- [x] Keep v1 simple
- [x] Leave room for v2
- [x] Make priorities visible to reviewers

## How
## Phase 1 - Completed
- Scaffold the repo structure for app code, data, diagrams, docs, and tests.
- Add seeded demo users, sample alerts, playbooks, asset data, and reputation data.
- Implement SQLite schema, seeding, RBAC, enrichment, scoring, incident lifecycle, and metrics.
- Build Streamlit screens for Reporter, Analyst, and Admin.
- Add CLI bootstrap and smoke workflow.

## Phase 2 - Next
- Add richer analyst search across assets, users, and prior alerts.
- Add admin reports export views and simple CSV export.
- Add score explanation panels directly in the UI.
- Add more timeline events to the audit log and expose them in the interface.

## Phase 3 - Later
- Replace seeded login with local auth and session handling.
- Add API routes that mirror the current service layer.
- Add attachment metadata handling beyond simple filenames.
- Add persistence choices better suited to multi-user concurrency.

## Phase 4 - Stretch
- Add simulated detections ingestion from JSONL or CSV feeds.
- Add analyst performance metrics and queue SLAs.
- Add rule tuning and detection configuration workflows.
- Add richer MITRE ATT&CK mapping and response playbook management.

## Delivery Notes
- The current best demo path is `Reporter -> Analyst -> Admin`.
- The current best verification path is `seed -> smoke -> Streamlit -> pytest`.
- The current known environment gap is that `pytest` is not installed in the active MSYS2 Python environment.

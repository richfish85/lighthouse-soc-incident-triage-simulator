# CHANGELOG

All notable changes to Lighthouse SOC are documented here.

## Unreleased

### Added
- Core app structure under `app/`, `data/`, `diagrams/`, `docs/`, `db/`, and `tests/`.
- SQLite schema for users, alerts, incidents, enrichment, notes, playbooks, and audit log.
- Seed loaders for demo users, sample incidents, asset context, IP reputation, and playbooks.
- RBAC helpers for `Reporter`, `Analyst`, and `Admin`.
- Service layer for alert intake, enrichment, scoring, incident lifecycle, playbooks, and metrics.
- Streamlit screens for login, reporter submission, alert tracking, analyst queue, investigation, playbooks, admin dashboard, and incident oversight.
- CLI commands for database init, bootstrap, seed, and smoke validation.
- Mermaid diagrams and walkthrough documentation.
- Root-level delivery docs: roadmap, architecture, threat model, detection ideas, and this changelog.

### Changed
- `README.md` was expanded from a one-line description into a full project guide.
- The repo now presents as a portfolio-ready security product demo instead of a starter folder.

### Validation
- `python -m app.cli smoke`
  Result: passed.
- `python -m compileall app tests`
  Result: passed.
- `python -m pytest`
  Result: blocked in the active environment because `pytest` is not installed.

### Notes
- The active Python runtime is MSYS2-managed and currently lacks a ready `pip` / `pytest` workflow for this repo.
- The code-level test suite is present and ready to run once the environment provides `pytest`.

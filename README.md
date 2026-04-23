# incident-triage-assistant

## What
Lighthouse SOC is a Python-based SOC triage simulator built inside `incident-triage-assistant/`.

It gives three role-based views:

- `Reporter` submits suspicious activity and tracks their own alerts
- `Analyst` triages the queue, investigates context, adds notes, and updates incident status
- `Admin` reviews metrics, trends, backlog health, and incident oversight

This is an MVP, so the goal is not to clone a full SIEM. The goal is to simulate a clean junior-SOC workflow from alert intake to investigation and oversight.

Example:

- A reporter submits `Impossible Travel Login`
- The system opens an incident, enriches it with asset and IP context, and scores priority
- An analyst reviews the playbook, adds notes, escalates or contains, and updates status
- An admin sees the effect in dashboard metrics and oversight tables

## Checklist
- [x] Role-based SOC workflow
- [x] SQLite-backed alert and incident data
- [x] Seeded demo users and sample incidents
- [x] Streamlit interface for Reporter, Analyst, and Admin
- [x] CLI smoke path for incident lifecycle validation
- [x] Mermaid diagrams and walkthrough docs for portfolio presentation

## Why
This project is designed to look and feel like a small security operations product instead of a script with a few forms.

The chosen stack is deliberate:

- `Python` keeps the business logic readable
- `SQLite` makes the demo self-contained
- `JSON` keeps seed data easy to inspect and extend
- `Streamlit` provides a fast way to deliver a polished interface and dashboard visuals

This also makes the repo useful as both:

- a build artifact you can run
- a portfolio artifact you can present and explain

## Checklist
- [x] Fast local setup
- [x] Clear service boundaries
- [x] Reusable scoring and RBAC logic
- [x] Strong demo story for interviews and portfolios

## How
The app is split into a few simple layers:

- `app/database.py` creates and resets the SQLite schema
- `app/seed.py` loads deterministic demo data
- `app/services/` owns intake, enrichment, scoring, incident lifecycle, playbooks, and metrics
- `app/ui/` keeps Streamlit pages thin by calling the service layer
- `app/cli.py` gives repeatable bootstrap and smoke-test commands

The priority algorithm is intentionally visible:

`severity + confidence + asset criticality + privileged account weight = priority`

Example:

- `High severity`
- `High confidence`
- `Critical asset`
- `Privileged account`

This produces a high numeric score and maps to `P1`.

## Checklist
- [x] Service-first design
- [x] Auto-open incident on alert creation
- [x] RBAC enforced in the service layer
- [x] Demo-friendly Streamlit navigation

## Quick Start
Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Seed the demo database:

```bash
python -m app.cli seed --reset
```

Run the Streamlit app:

```bash
streamlit run app/main.py
```

Run the CLI smoke path:

```bash
python -m app.cli smoke
```

Run tests:

```bash
python -m pytest
```

## Checklist
- [ ] Install dependencies
- [ ] Seed the database
- [ ] Launch Streamlit
- [ ] Run the smoke path
- [ ] Run pytest

## Demo Users
Use these seeded accounts from the login gateway:

- `reporter01` - Mia Santos - Reporter
- `analyst01` - Jordan Kim - Analyst
- `admin01` - Riley Chen - Admin

## MVP Screens
- `Login / Role Gateway`
- `Reporter / Submit Alert`
- `Reporter / My Submitted Alerts`
- `Analyst / Queue`
- `Analyst / Incident Investigation View`
- `Analyst / Playbooks`
- `Admin / Dashboard`
- `Admin / Incident Oversight`

## Sample Incident Scenarios
- `Impossible Travel Login`
- `Malware Detection`
- `Phishing Reported`
- `Suspicious PowerShell`
- `Repeated Failed Logins`
- `Privilege Escalation Attempt`

## Project Structure
```text
incident-triage-assistant/
├── app/
│   ├── main.py
│   ├── cli.py
│   ├── auth.py
│   ├── roles.py
│   ├── database.py
│   ├── models.py
│   ├── seed.py
│   ├── services/
│   └── ui/
├── data/
├── diagrams/
├── docs/
├── db/
└── tests/
```

## Diagrams And Walkthrough
- Architecture: [diagrams/architecture.mmd](diagrams/architecture.mmd)
- RBAC matrix: [diagrams/rbac-matrix.mmd](diagrams/rbac-matrix.mmd)
- Incident lifecycle: [diagrams/incident-lifecycle.mmd](diagrams/incident-lifecycle.mmd)
- Screen flow: [diagrams/screen-flow.mmd](diagrams/screen-flow.mmd)
- Portfolio walkthrough: [docs/walkthrough.md](docs/walkthrough.md)

## Project Documents
- Delivery roadmap: [ROADMAP.md](ROADMAP.md)
- System architecture: [ARCHITECTURE.md](ARCHITECTURE.md)
- Implementation log: [CHANGELOG.md](CHANGELOG.md)
- Threat model: [THREAT_MODEL.md](THREAT_MODEL.md)
- Future detection ideas: [DETECTION_IDEAS.md](DETECTION_IDEAS.md)

## Validation
Current validation targets:

- `python -m pytest`
- `python -m app.cli smoke`
- `streamlit run app/main.py`

## Screenshot Checklist
- [ ] Login and role gateway
- [ ] Reporter submits a new alert
- [ ] Analyst queue with priorities and filters
- [ ] Investigation view with enrichment and playbook
- [ ] Admin dashboard metrics and charts
- [ ] Incident oversight table

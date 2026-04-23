# Lighthouse SOC Walkthrough

## What
This walkthrough explains how the Lighthouse SOC MVP is structured, how to run it, and how to present it as a clean portfolio project.

Think of it as two things at once:

- a build guide
- a presentation guide

Example:

- Start as `reporter01`
- submit a suspicious login alert
- switch to `analyst01`
- investigate and update the incident
- switch to `admin01`
- review the dashboard impact

## Checklist
- [ ] Read the implementation overview
- [ ] Run the seed step
- [ ] Walk through each role once
- [ ] Capture screenshots for the portfolio set

## Why
The app is intentionally scoped to junior-SOC triage.

That keeps the demo believable and easy to explain:

- alerts come in
- incidents get enriched and prioritised
- analysts work from a queue
- admins review performance and trends

This is much easier to present professionally than a half-finished “full SIEM” claim.

## Checklist
- [x] Focused scope
- [x] Clear product story
- [x] Interview-friendly demo flow

## How
Run these commands from the repo root:

```bash
python -m pip install -r requirements.txt
python -m app.cli seed --reset
streamlit run app/main.py
```

Optional validation:

```bash
python -m app.cli smoke
python -m pytest
```

## Checklist
- [ ] Install dependencies
- [ ] Seed the database
- [ ] Launch Streamlit
- [ ] Run smoke validation
- [ ] Run tests

## Implementation
- `app/database.py` owns schema creation and reset helpers.
- `app/seed.py` loads users, playbooks, assets, IP reputation, and sample alerts.
- `app/services/intake.py` creates alerts and auto-opens incidents.
- `app/services/enrichment.py` adds context from sample assets, identity profiles, and IP reputation data.
- `app/services/scoring.py` converts severity, confidence, asset criticality, and account type into `P1` to `P5`.
- `app/services/incidents.py` handles assignment, notes, escalation, and status transitions.
- `app/services/metrics.py` builds chart-ready data for the admin dashboard.
- `app/ui/` contains the Streamlit screens for each role.

## Assumptions
- The app uses seeded demo users instead of real authentication.
- Sample data is fictional and designed for demonstration.
- Streamlit is acceptable for the MVP even though it is not a production multi-user web front end.
- File uploads are mocked as metadata only.

## Threat/Risk Notes
- Role switching in the UI is only a demo convenience, so RBAC is enforced in the service layer as well.
- SQLite is fine for a local demo but not for real concurrent analyst operations.
- Streamlit page visibility is not a security boundary.
- Sample incident content should remain fictional if you extend the dataset.

## Validation Steps
- Seed the database with `python -m app.cli seed --reset`.
- Run the smoke path with `python -m app.cli smoke`.
- Run automated checks with `python -m pytest`.
- Run the app with `streamlit run app/main.py`.
- Confirm the reporter only sees their own alerts.
- Confirm analysts can assign, note, escalate, contain, and close incidents.
- Confirm admins can see metrics and oversight for all incidents.

## Demo Script
### Reporter
- Log in as `reporter01`.
- Open `Submit Alert`.
- Create a new `Phishing Reported` or `Impossible Travel Login` alert.
- Open `My Alerts` and confirm the new record appears.

### Analyst
- Log in as `analyst01`.
- Open `Queue`.
- Filter by severity or assigned state.
- Open `Incident Investigation View`.
- Add a note, assign the incident, and change status.

### Admin
- Log in as `admin01`.
- Open `Dashboard`.
- Review total alerts, open incidents, critical incidents, and false positive rate.
- Open `Incident Oversight` and inspect the latest notes on a selected record.

## Portfolio Capture Checklist
- [ ] Hero login screen
- [ ] Reporter submission form
- [ ] Reporter alert detail with status
- [ ] Analyst queue with P1 and escalated items visible
- [ ] Investigation screen with three-column layout
- [ ] Playbooks screen
- [ ] Admin dashboard charts
- [ ] Incident oversight screen

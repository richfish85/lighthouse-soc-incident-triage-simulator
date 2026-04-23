# THREAT_MODEL

## What
This document captures the main security assumptions and risks for Lighthouse SOC as an MVP simulator.

This is not a production hardening plan.

It is a structured review of:

- what we are protecting
- what could go wrong
- what is already mitigated
- what is intentionally deferred

## Checklist
- [x] Identify protected assets
- [x] Identify trust boundaries
- [x] Call out demo-only assumptions
- [x] Record deferred risks

## Why
Security tooling looks stronger when the project also shows security thinking.

For a project like this, the value is not just the UI.

The value is also showing that we understand:

- access control
- data sensitivity
- environment limits
- where the MVP is intentionally weak

## Checklist
- [x] Professional security framing
- [x] Honest MVP limitations
- [x] Clear mitigation direction

## How
## Protected Assets
- Incident data
- Reporter submissions
- Analyst notes
- Role permissions
- Audit trail integrity
- Playbook guidance and triage history

## Trust Boundaries
- User interaction in Streamlit
- Service-layer business logic
- SQLite persistence layer
- Seeded JSON sample data

## Threat Scenarios
### 1. Role bypass through UI-only controls
- Risk:
  a user sees or triggers actions they should not have based only on page visibility.
- Current mitigation:
  RBAC checks are enforced in the service layer, not only in the UI.
- Remaining gap:
  seeded login is still a demo convenience, not strong authentication.

### 2. Unauthorized access to other reporter records
- Risk:
  a reporter attempts to view incidents or alerts outside their scope.
- Current mitigation:
  reporter alert retrieval is filtered by `reporter_user_id`.
- Remaining gap:
  there is no production-grade session boundary or identity proofing.

### 3. Tampering with incident state
- Risk:
  incident status, assignment, or notes could be changed without a trace.
- Current mitigation:
  key incident actions are recorded in `audit_log`.
- Remaining gap:
  the audit log is not signed, replicated, or protected from a privileged local operator.

### 4. Malicious or unsafe file handling
- Risk:
  uploaded evidence could introduce unsafe file-processing paths.
- Current mitigation:
  v1 stores evidence as metadata only, not as uploaded binary content.
- Remaining gap:
  real attachment support is deferred.

### 5. Data leakage through sample content
- Risk:
  demo data accidentally resembles real people or infrastructure.
- Current mitigation:
  the project uses fictional users, assets, and reserved documentation IP ranges.
- Remaining gap:
  new sample content still needs review when added.

### 6. Concurrency and data integrity limits
- Risk:
  SQLite and local state become unreliable under true multi-user load.
- Current mitigation:
  project scope is explicitly local-demo first.
- Remaining gap:
  production concurrency controls are out of scope for this MVP.

## Assumptions
- This app runs locally for demo, learning, or portfolio use.
- Demo users are trusted enough for role-switch simulation.
- The environment is not exposed as a public production service.

## Validation Steps
- Review service-layer permission checks in `app/roles.py`, `app/auth.py`, and service modules.
- Confirm reporters only see their own alert records in the UI.
- Confirm analysts can update incidents while reporters cannot.
- Review `audit_log` after smoke tests to confirm lifecycle actions are captured.
- Re-run tests after `pytest` is available in the environment.

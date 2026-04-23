# DETECTION_IDEAS

## What
This file tracks future alert and detection ideas that could expand Lighthouse SOC without breaking the current MVP.

The goal is not to add everything at once.

The goal is to grow the simulator in ways that still feel realistic and teachable.

## Checklist
- [x] Keep ideas grouped by use case
- [x] Keep ideas compatible with the current scoring model
- [x] Prefer portfolio-friendly detections

## Why
Detection ideas help in two ways:

- they create a practical backlog for future work
- they show product thinking beyond the current implementation

Example:

- today the app supports six core incident scenarios
- tomorrow the same structure can support cloud, identity, email, and endpoint detections

## Checklist
- [x] Preserve current MVP
- [x] Leave room for richer scenarios
- [x] Connect ideas to future demos

## How
## Identity And Access
- MFA fatigue detected
  Why it fits:
  pairs well with impossible travel and account takeover stories.
- Password spray across multiple users
  Why it fits:
  extends repeated failed logins into a richer analyst queue pattern.
- Dormant privileged account reactivation
  Why it fits:
  good for admin oversight and priority scoring demos.

## Endpoint And Execution
- Unsigned binary execution from temp paths
- Suspicious scheduled task creation
- Office macro spawning script interpreter
- Defense evasion through log clearing

These would fit naturally into the current `Execution` and `Privilege Escalation` style workflows.

## Email And User-Reported
- Business email compromise indicators
- QR-code phishing
- OAuth consent phishing
- Bulk user-reported phishing cluster

These would make the reporter workflow more varied and visually strong.

## Cloud And SaaS
- Impossible travel in SaaS admin console
- Suspicious mailbox forwarding rule
- New high-privilege API token creation
- Storage bucket made public unexpectedly

These would help the project feel more current and modern.

## Detection Logic Ideas
- Add severity modifiers for:
  privileged account
  crown-jewel asset
  malicious IP
  repeat offender pattern
  after-hours activity
- Add confidence modifiers for:
  multiple telemetry sources agreeing
  repeated alerts in a short time window
  user confirmation or denial

## Mapping Ideas
- Link each alert type to:
  MITRE tactic
  MITRE technique
  response playbook
  sample analyst questions

## Good Next Additions
- `MFA Fatigue`
- `Mailbox Forwarding Rule`
- `Unsigned Binary Execution`
- `Password Spray`

These four would expand the simulator meaningfully without changing the app structure.

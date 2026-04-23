# Lighthouse SOC — Incident Triage Simulator

*A Python-based incident triage simulator demonstrating software engineering, systems design, and security workflow simulation and automation concepts.*

**Built as a learning project to demonstrate software engineering fundamentals relevant to junior technical engineering roles.**


## What is this?

**Lighthouse SOC** is a lightweight security operations simulation platform built to model how incidents move from reporting to investigation and oversight.

Rather than replicating a full SIEM, this project focuses on core engineering concepts:

* Role-based workflows
* Data modelling with SQLite
* Python service-layer architecture
* Incident scoring logic
* CLI tooling and testing
* Interactive dashboard development with Streamlit

It simulates three user roles:

### Reporter

* Submit suspicious activity reports
* Track submitted alerts
* View incident outcomes

### Analyst

* Triage incoming incidents
* Review enrichment context
* Apply playbooks
* Add notes and update status

### Admin

* Review incident trends
* Monitor backlog health
* View operational metrics and oversight dashboards

---

# Why I Built This

This project was designed as both:

## 1. A Software Engineering Portfolio Project

To demonstrate practical skills in:

* Python development
* SQL and data modelling
* Service-oriented design
* CLI tooling
* Testing and debugging
* UI prototyping

## 2. A Systems Thinking Exercise

To model how software components interact:

* Intake → Processing → Scoring → Workflow → Reporting

It intentionally emphasizes clean architecture over complexity.

---

# Example Workflow

Example incident:

**Impossible Travel Login**

1. Reporter submits alert
2. System opens incident record
3. Asset/IP context is enriched
4. Priority is calculated
5. Analyst investigates and updates status
6. Admin dashboards reflect incident impact

---

# Core Features

## Implemented

* Role-based workflow simulation
* SQLite-backed incident and alert data
* Streamlit UI with three user views
* Seeded demo data and users
* Priority scoring engine
* CLI smoke tests
* Pytest validation
* Mermaid architecture diagrams

---

# Tech Stack

| Area     | Technology      |
| -------- | --------------- |
| Language | Python          |
| Data     | SQLite, JSON    |
| UI       | Streamlit       |
| Testing  | Pytest          |
| Diagrams | Mermaid         |
| CLI      | Python argparse |

---

# Architecture

Project uses a simple service-first structure:

```text
app/
├── main.py
├── cli.py
├── database.py
├── seed.py
├── services/
├── ui/
└── tests/
```

### Layers

**Database**

* Schema creation
* Seed loading
* Persistence

**Services**

* Alert intake
* Enrichment
* Scoring
* Incident lifecycle
* Metrics

**UI**

* Thin presentation layer over services

**CLI**

* Bootstrap
* Smoke tests
* Validation flows

---

# Priority Scoring Logic

Priority is intentionally transparent:

```text
Severity
+ Confidence
+ Asset Criticality
+ Privileged Account Weight
= Priority Score
```

Example:

High severity
High confidence
Critical asset
Privileged account

→ maps to **P1**

---

# Quick Start

## Install

```bash
python -m pip install -r requirements.txt
```

## Seed Demo Data

```bash
python -m app.cli seed --reset
```

## Run App

```bash
streamlit run app/main.py
```

## Run Smoke Tests

```bash
python -m app.cli smoke
```

## Run Test Suite

```bash
python -m pytest
```

---

# Demo Accounts

| User       | Role     |
| ---------- | -------- |
| reporter01 | Reporter |
| analyst01  | Analyst  |
| admin01    | Admin    |

---

# Sample Incident Scenarios

* Impossible Travel Login
* Malware Detection
* Phishing Reported
* Suspicious PowerShell
* Repeated Failed Logins
* Privilege Escalation Attempt

---

# Documentation

## Diagrams

* Architecture
* RBAC Matrix
* Incident Lifecycle
* Screen Flow

Located in:

```text
diagrams/
```

## Supporting Docs

* ROADMAP.md
* ARCHITECTURE.md
* THREAT_MODEL.md
* DETECTION_IDEAS.md

---

# Validation

```bash
python -m pytest
python -m app.cli smoke
streamlit run app/main.py
```

---


# Engineering Principles Demonstrated

This project applies:
- Modular software design
- Role-based access concepts
- Data modelling and persistence
- Test-driven validation
- Reproducible CLI workflows
- Secure-by-design thinking

# Design Tradeoffs

This MVP deliberately uses:

- SQLite over PostgreSQL for portability
- Streamlit over heavier frontend stacks for rapid prototyping
- Rule-based scoring over ML for transparency and explainability

# Future Extensions

Planned ideas:
* Audit logging
* Identity integration (SSO / RBAC expansion)
* Case management workflow
* Policy compliance mapping
* MITRE ATT&CK mapping
* IOC enrichment integrations
* Simulated case management
* Detection rule tuning
* Expanded RBAC permissions
* API-backed alert sources

---

# Why This Project Matters

This project reflects the same foundational areas emphasized in junior engineering pathways:

* Programming fundamentals
* Data and logic modelling
* APIs and service thinking
* Debugging and testing
* System decomposition
* Secure workflow design

It was built as a practical learning project and as a stepping stone toward software engineering and technical operations roles.

---

## Screenshots


<img width="1845" height="918" alt="image" src="https://github.com/user-attachments/assets/7e031f33-b5b5-41b6-b990-24d4ad39d6ae" />
### Login gateway


<img width="1919" height="907" alt="image" src="https://github.com/user-attachments/assets/dd67d515-bcda-4022-bedf-cab6784f5ca6" />
### Analyst queue


<img width="1919" height="906" alt="image" src="https://github.com/user-attachments/assets/b275dc24-e6ec-481e-b68b-ac510645e26d" />
### Investigation view


<img width="1919" height="908" alt="image" src="https://github.com/user-attachments/assets/9d9e72fd-e6de-4a23-aa09-d87f5c6832c9" />
### Admin dashboard

---

## Author

Richard Fisher
GitHub: [https://github.com/richfish85](https://github.com/richfish85)



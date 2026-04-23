"""Analyst-facing Streamlit screens."""

from __future__ import annotations

import streamlit as st

from app.services.incidents import (
    INCIDENT_STATUSES,
    add_note,
    assign_incident,
    escalate_incident,
    get_incident,
    list_incidents,
    update_status,
)
from app.services.playbooks import list_playbooks


def _format_incident_option(incident_id: str, incidents: list[dict[str, object]]) -> str:
    incident = next(item for item in incidents if item["incident_id"] == incident_id)
    return f"{incident_id} | {incident['priority']} | {incident['alert_type']} | {incident['incident_status']}"


def render_queue(user: dict[str, object]) -> None:
    """Render the analyst queue screen."""
    all_incidents = list_incidents(user)
    st.title("Analyst Queue")
    st.caption("Prioritise what needs attention first and move quickly into the investigation view.")

    if not all_incidents:
        st.info("No incidents in the queue right now.")
        return

    severity_options = ["All"] + sorted({str(item["severity"]) for item in all_incidents})
    status_options = ["All"] + list(INCIDENT_STATUSES)

    first, second, third = st.columns(3)
    with first:
        severity_filter = st.selectbox("Severity", severity_options)
    with second:
        status_filter = st.selectbox("Status", status_options)
    with third:
        assigned_to_me = st.checkbox("Assigned to me only")

    filters = {}
    if severity_filter != "All":
        filters["severity"] = severity_filter
    if status_filter != "All":
        filters["status"] = status_filter
    if assigned_to_me:
        filters["assigned_to_me"] = True

    incidents = list_incidents(user, filters)

    total_open = sum(1 for incident in incidents if incident["incident_status"] not in {"Closed", "False Positive"})
    p1_count = sum(1 for incident in incidents if incident["priority"] == "P1")
    escalated = sum(1 for incident in incidents if incident["incident_status"] == "Escalated")
    first_card, second_card, third_card = st.columns(3)
    first_card.metric("Visible Incidents", len(incidents))
    second_card.metric("Open", total_open)
    third_card.metric("P1 / Escalated", f"{p1_count} / {escalated}")

    st.dataframe(
        [
            {
                "Priority": incident["priority"],
                "Incident ID": incident["incident_id"],
                "Alert Type": incident["alert_type"],
                "Severity": incident["severity"],
                "Confidence": incident["confidence"],
                "Status": incident["incident_status"],
                "Assigned": incident["assignee_name"] or "Unassigned",
                "Age": incident["age"],
            }
            for incident in incidents
        ],
        use_container_width=True,
        hide_index=True,
    )

    incident_ids = [item["incident_id"] for item in incidents]
    selected_id = st.selectbox(
        "Choose incident",
        incident_ids,
        index=incident_ids.index(st.session_state.get("selected_incident_id", incident_ids[0]))
        if st.session_state.get("selected_incident_id") in incident_ids
        else 0,
        format_func=lambda incident_id: _format_incident_option(incident_id, incidents),
    )
    st.session_state["selected_incident_id"] = selected_id

    left, middle, right = st.columns(3)
    if left.button("Open Investigation", use_container_width=True):
        st.session_state["nav_page"] = "Investigation"
        st.rerun()
    if middle.button("Assign to Me", use_container_width=True):
        assign_incident(selected_id, str(user["username"]), user)
        st.success(f"{selected_id} assigned to {user['username']}.")
        st.rerun()
    if right.button("Escalate", use_container_width=True):
        escalate_incident(selected_id, user, "Escalated from analyst queue for deeper review.")
        st.success(f"{selected_id} escalated.")
        st.rerun()


def render_investigation(user: dict[str, object]) -> None:
    """Render the analyst incident detail screen."""
    incidents = list_incidents(user)
    st.title("Incident Investigation View")
    st.caption("Review context, capture notes, and update the incident lifecycle from one workspace.")

    if not incidents:
        st.info("No incidents are available for investigation.")
        return

    incident_ids = [item["incident_id"] for item in incidents]
    current_id = st.session_state.get("selected_incident_id", incident_ids[0])
    selected_id = st.selectbox(
        "Active incident",
        incident_ids,
        index=incident_ids.index(current_id) if current_id in incident_ids else 0,
        format_func=lambda incident_id: _format_incident_option(incident_id, incidents),
    )
    st.session_state["selected_incident_id"] = selected_id
    incident = get_incident(selected_id, user)

    left, middle, right = st.columns((1.1, 1.1, 1.1))
    with left:
        st.subheader("Incident Summary")
        st.markdown(f"**Incident ID**: {incident['incident_id']}")
        st.markdown(f"**Alert ID**: {incident['alert_id']}")
        st.markdown(f"**Alert Type**: {incident['alert_type']}")
        st.markdown(f"**Affected User**: {incident['affected_user']}")
        st.markdown(f"**Source IP**: {incident['source_ip']}")
        st.markdown(f"**Asset**: {incident['affected_asset']}")
        st.markdown(f"**Event Count**: {incident['event_count']}")
        st.markdown(f"**MITRE Tactic**: {incident['mitre_tactic']}")
        st.markdown(f"**Assigned Analyst**: {incident['assignee_name'] or 'Unassigned'}")

    with middle:
        st.subheader("Enrichment & Context")
        st.metric("IP Reputation", incident["ip_reputation"])
        st.metric("Geo", incident["geo_location"])
        st.metric("User Baseline", incident["user_typical_location"])
        st.metric("Asset Criticality", incident["asset_criticality"])
        st.metric("Account Type", incident["account_type"])
        st.metric("Repeat Alerts", incident["repeat_alert_count"])
        st.caption(incident["enrichment_notes"])

    with right:
        st.subheader("Recommended Actions")
        st.markdown(f"**Playbook**: {incident['playbook']['title']}")
        st.markdown(f"**Severity Hint**: {incident['playbook']['severity_hint']}")
        for index, step in enumerate(incident["playbook"]["steps"], start=1):
            st.markdown(f"{index}. {step}")

    actions_left, actions_right = st.columns((1.2, 1))
    with actions_left:
        st.subheader("Investigation Notes")
        with st.form("add_note_form"):
            note_content = st.text_area("Add note", height=120, placeholder="Capture analyst findings, user contact, or containment steps.")
            reporter_visible = st.checkbox("Visible to reporter")
            save_note = st.form_submit_button("Save Notes", use_container_width=True)
        if save_note:
            add_note(selected_id, user, note_content, visible_to_reporter=reporter_visible)
            st.success("Investigation note saved.")
            st.rerun()

        if incident["notes"]:
            for note in incident["notes"]:
                st.markdown(
                    f"**{note['created_at']} · {note['author_full_name']} · {note['note_type']}**  \n"
                    f"{note['content']}"
                )
        else:
            st.info("No notes yet.")

    with actions_right:
        st.subheader("Status Controls")
        st.metric("Priority", incident["priority"])
        st.metric("Severity", incident["severity"])
        st.metric("Confidence", incident["confidence"])

        if st.button("Assign to Me", use_container_width=True):
            assign_incident(selected_id, str(user["username"]), user)
            st.success("Incident assigned.")
            st.rerun()

        with st.form("status_form"):
            new_status = st.selectbox("Update status", INCIDENT_STATUSES, index=INCIDENT_STATUSES.index(incident["incident_status"]))
            status_reason = st.text_area("Escalation reason", height=90, placeholder="Optional context for escalation or closure.")
            status_submitted = st.form_submit_button("Apply Change", use_container_width=True)

        if status_submitted:
            if new_status == "Escalated":
                escalate_incident(selected_id, user, status_reason)
            else:
                update_status(selected_id, new_status, user)
                if status_reason.strip():
                    add_note(selected_id, user, status_reason, note_type="system_note")
            st.success(f"Incident updated to {new_status}.")
            st.rerun()


def render_playbooks(user: dict[str, object]) -> None:
    """Render the analyst playbook reference screen."""
    playbooks = list_playbooks(user)
    st.title("Playbooks")
    st.caption("Reference response guidance by alert type while triaging incidents.")

    if not playbooks:
        st.info("No playbooks are available.")
        return

    alert_types = [playbook["alert_type"] for playbook in playbooks]
    selected_alert_type = st.selectbox("Choose playbook", alert_types)
    playbook = next(item for item in playbooks if item["alert_type"] == selected_alert_type)

    left, right = st.columns((1.2, 1))
    with left:
        st.subheader(playbook["title"])
        st.markdown(f"**Alert Type**: {playbook['alert_type']}")
        st.markdown(f"**Severity Hint**: {playbook['severity_hint']}")
        for index, step in enumerate(playbook["steps"], start=1):
            st.markdown(f"{index}. {step}")
    with right:
        st.subheader("Available Playbooks")
        st.dataframe(
            [
                {
                    "Alert Type": item["alert_type"],
                    "Title": item["title"],
                    "Severity Hint": item["severity_hint"],
                }
                for item in playbooks
            ],
            use_container_width=True,
            hide_index=True,
        )

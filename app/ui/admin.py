"""Admin-facing Streamlit screens."""

from __future__ import annotations

import streamlit as st

from app.services.incidents import INCIDENT_STATUSES, get_incident, list_incidents
from app.services.metrics import get_dashboard_metrics


def _render_bar_chart(title: str, values: list[dict[str, object]], x_key: str, y_key: str, color: str) -> None:
    st.subheader(title)
    st.vega_lite_chart(
        {
            "data": {"values": values},
            "mark": {"type": "bar", "cornerRadiusTopLeft": 6, "cornerRadiusTopRight": 6, "color": color},
            "encoding": {
                "x": {"field": x_key, "type": "nominal", "sort": "-y"},
                "y": {"field": y_key, "type": "quantitative"},
                "tooltip": [{"field": x_key, "type": "nominal"}, {"field": y_key, "type": "quantitative"}],
            },
        },
        use_container_width=True,
    )


def _render_line_chart(title: str, values: list[dict[str, object]], color: str) -> None:
    st.subheader(title)
    st.vega_lite_chart(
        {
            "data": {"values": values},
            "mark": {"type": "line", "point": True, "color": color},
            "encoding": {
                "x": {"field": "day", "type": "temporal"},
                "y": {"field": "count", "type": "quantitative"},
                "tooltip": [{"field": "day", "type": "temporal"}, {"field": "count", "type": "quantitative"}],
            },
        },
        use_container_width=True,
    )


def _render_arc_chart(title: str, values: list[dict[str, object]]) -> None:
    st.subheader(title)
    st.vega_lite_chart(
        {
            "data": {"values": values},
            "mark": {"type": "arc", "innerRadius": 45},
            "encoding": {
                "theta": {"field": "count", "type": "quantitative"},
                "color": {
                    "field": "status",
                    "type": "nominal",
                    "scale": {"range": ["#d6b25e", "#4f8a8b", "#c56c5b", "#718096", "#2f855a", "#8b5cf6"]},
                },
                "tooltip": [{"field": "status", "type": "nominal"}, {"field": "count", "type": "quantitative"}],
            },
        },
        use_container_width=True,
    )


def render_dashboard(user: dict[str, object]) -> None:
    """Render the admin dashboard screen."""
    metrics = get_dashboard_metrics(user)
    totals = metrics["totals"]

    st.title("Admin Dashboard")
    st.caption("Review team workload, triage quality, and incident trends across the SOC simulation.")

    first, second, third = st.columns(3)
    fourth, fifth, sixth = st.columns(3)
    first.metric("Total Alerts", totals["total_alerts"])
    second.metric("Open Incidents", totals["open_incidents"])
    third.metric("Critical Incidents", totals["critical_incidents"])
    fourth.metric("Escalations", totals["escalations"])
    fifth.metric("Mean Triage Time", f"{totals['mean_triage_minutes']} min")
    sixth.metric("False Positive Rate", f"{totals['false_positive_rate']}%")

    top_left, top_right = st.columns(2)
    bottom_left, bottom_right = st.columns(2)
    with top_left:
        _render_bar_chart("Alerts by Severity", metrics["alerts_by_severity"], "severity", "count", "#d6b25e")
    with top_right:
        _render_line_chart("Alert Trends Over Time", metrics["alert_trends"], "#4f8a8b")
    with bottom_left:
        _render_bar_chart("Top Alert Types", metrics["top_alert_types"], "alert_type", "count", "#c56c5b")
    with bottom_right:
        _render_arc_chart("Incident Status Distribution", metrics["status_breakdown"])


def render_incident_oversight(user: dict[str, object]) -> None:
    """Render the admin oversight table and selected incident snapshot."""
    all_incidents = list_incidents(user)
    st.title("Incident Oversight")
    st.caption("Review backlog health, unresolved criticals, and ownership across the demo SOC.")

    if not all_incidents:
        st.info("No incidents are available.")
        return

    status_options = ["All"] + list(INCIDENT_STATUSES)
    assignee_options = ["All"] + sorted({incident["assignee_username"] or "Unassigned" for incident in all_incidents})
    priority_options = ["All"] + sorted({incident["priority"] for incident in all_incidents})

    left, middle, right = st.columns(3)
    with left:
        status_filter = st.selectbox("Status", status_options)
    with middle:
        assignee_filter = st.selectbox("Assignee", assignee_options)
    with right:
        priority_filter = st.selectbox("Priority", priority_options)

    filters = {}
    if status_filter != "All":
        filters["status"] = status_filter
    if assignee_filter != "All" and assignee_filter != "Unassigned":
        filters["assignee_username"] = assignee_filter
    if priority_filter != "All":
        filters["priority"] = priority_filter

    incidents = list_incidents(user, filters)
    st.dataframe(
        [
            {
                "Incident ID": incident["incident_id"],
                "Priority": incident["priority"],
                "Alert Type": incident["alert_type"],
                "Status": incident["incident_status"],
                "Assigned": incident["assignee_name"] or "Unassigned",
                "Affected Asset": incident["affected_asset"],
                "Backlog Age": incident["age"],
            }
            for incident in incidents
        ],
        use_container_width=True,
        hide_index=True,
    )

    incident_ids = [incident["incident_id"] for incident in incidents]
    if not incident_ids:
        st.warning("No incidents matched those filters.")
        return

    selected_id = st.selectbox("Inspect incident", incident_ids)
    incident = get_incident(selected_id, user)

    left_panel, right_panel = st.columns((1.1, 1))
    with left_panel:
        st.subheader("Oversight Snapshot")
        st.markdown(f"**Priority**: {incident['priority']}")
        st.markdown(f"**Alert Type**: {incident['alert_type']}")
        st.markdown(f"**Assigned Analyst**: {incident['assignee_name'] or 'Unassigned'}")
        st.markdown(f"**Status**: {incident['incident_status']}")
        st.markdown(f"**Escalation Level**: {incident['escalation_level']}")
        st.markdown(f"**Asset Criticality**: {incident['asset_criticality']}")
        st.markdown(f"**Reporter**: {incident['reporter_name']}")
        st.markdown(f"**Last Updated**: {incident['updated_at']}")
    with right_panel:
        st.subheader("Latest Notes")
        if incident["notes"]:
            for note in incident["notes"][-4:]:
                st.markdown(
                    f"**{note['created_at']} · {note['author_full_name']}**  \n"
                    f"{note['content']}"
                )
        else:
            st.info("No notes recorded yet.")

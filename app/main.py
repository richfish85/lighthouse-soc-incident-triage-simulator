"""Streamlit entry point for Lighthouse SOC."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st

from app.auth import list_demo_users, login_demo_user
from app.seed import bootstrap_demo_data
from app.services.incidents import list_incidents
from app.services.intake import list_reporter_alerts
from app.ui import admin, analyst, reporter, shell


st.set_page_config(page_title="Lighthouse SOC", layout="wide", initial_sidebar_state="collapsed")


ANALYST_PAGE_DEFS = [
    {
        "key": "analyst_queue",
        "title": "Queue",
        "icon": ":material/view_list:",
        "url_path": "analyst-queue",
        "default": True,
        "label": "Queue",
    },
    {
        "key": "analyst_investigation",
        "title": "Investigation",
        "icon": ":material/manage_search:",
        "url_path": "analyst-investigation",
        "label": "Investigation",
    },
    {
        "key": "analyst_playbooks",
        "title": "Playbooks",
        "icon": ":material/menu_book:",
        "url_path": "analyst-playbooks",
        "label": "Playbooks",
    },
]


ADMIN_PAGE_DEFS = [
    {
        "key": "admin_dashboard",
        "title": "Dashboard",
        "icon": ":material/space_dashboard:",
        "url_path": "admin-dashboard",
        "default": True,
        "label": "Dashboard",
    },
    {
        "key": "admin_incident_oversight",
        "title": "Incident Oversight",
        "icon": ":material/monitoring:",
        "url_path": "admin-incident-oversight",
        "label": "Incident Oversight",
    },
]


ROLE_PAGE_DEFS = {
    "Reporter": reporter.REPORTER_PAGE_DEFS,
    "Analyst": ANALYST_PAGE_DEFS,
    "Admin": ADMIN_PAGE_DEFS,
}


def _clear_session_for_logout() -> None:
    for key in (
        "current_username",
        "selected_incident_id",
        "selected_alert_id",
        "reporter_wizard",
        "reporter_submission_success",
    ):
        st.session_state.pop(key, None)


def _render_login(users: list[dict[str, object]]) -> None:
    st.html(
        f"""
        <section class="portal-header">
          <div class="portal-brand">
            {shell.logo_svg()}
            <div class="portal-brand-copy">
              <div class="portal-brand-title">LIGHTHOUSE <span>SOC</span></div>
              <div class="portal-brand-subtitle">Navigate the noise</div>
            </div>
          </div>
          <div class="portal-header-actions">
            <div class="portal-action">Role-based triage simulator</div>
            <div class="portal-action">Reporter · Analyst · Admin</div>
          </div>
        </section>
        """
    )

    left, right = st.columns([1.45, 1], gap="large")
    with left:
        shell.render_page_intro(
            "Security operations, minus the clutter.",
            "Lighthouse SOC simulates a believable junior-SOC workflow: report suspicious activity, triage incidents, investigate context, and review operational metrics.",
            eyebrow="Portfolio Demo",
        )
        with st.container(border=True):
            st.subheader("What you can do here")
            st.write("Submit new alerts, review your own reports, investigate incidents as an analyst, and see the platform from an admin/SOC lead point of view.")
            shell.render_stat_grid(
                [
                    ("Roles", "3"),
                    ("Seed Incidents", "6"),
                    ("Workflows", "Reporter · Analyst · Admin"),
                ]
            )
    with right:
        with st.container(border=True):
            st.subheader("Login / Role Gateway")
            st.caption("Use seeded demo users to enter the platform.")
            selected_username = st.selectbox(
                "Choose a demo user",
                [user["username"] for user in users],
                format_func=lambda username: next(
                    f"{username} · {user['role']} · {user['full_name']}" for user in users if user["username"] == username
                ),
            )
            if st.button("Login", type="primary", use_container_width=True):
                st.session_state["current_username"] = selected_username
                st.rerun()


def _notification_count(user: dict[str, object]) -> int:
    if str(user["role"]) == "Reporter":
        alerts = list_reporter_alerts(user)
        return sum(1 for alert in alerts if alert["status"] not in reporter.CLOSED_STATUSES)
    if str(user["role"]) == "Analyst":
        incidents = list_incidents(user, {"assigned_to_me": True})
        return sum(1 for incident in incidents if incident["incident_status"] not in {"Closed", "False Positive"})
    incidents = list_incidents(user)
    return sum(1 for incident in incidents if incident["incident_status"] not in {"Closed", "False Positive"})


def _build_reporter_pages(user: dict[str, object]) -> dict[str, object]:
    page_registry: dict[str, object] = {}
    for page_def in reporter.REPORTER_PAGE_DEFS:
        renderer = {
            "reporter_new_alert": lambda user=user, registry=page_registry: reporter.render_new_alert(user, registry),
            "reporter_my_alerts": lambda user=user, registry=page_registry: reporter.render_my_alerts(user, registry),
            "reporter_alert_status": lambda user=user, registry=page_registry: reporter.render_alert_status(user, registry),
            "reporter_faq": lambda user=user, registry=page_registry: reporter.render_faq_guidance(user, registry),
            "reporter_contact_soc": lambda user=user, registry=page_registry: reporter.render_contact_soc(user, registry),
        }[page_def["key"]]
        page_registry[page_def["key"]] = st.Page(
            renderer,
            title=page_def["title"],
            icon=page_def["icon"],
            url_path=page_def["url_path"],
            default=page_def.get("default", False),
        )
    return page_registry


def _build_analyst_pages(user: dict[str, object]) -> dict[str, object]:
    return {
        "analyst_queue": st.Page(
            lambda user=user: analyst.render_queue(user),
            title="Queue",
            icon=":material/view_list:",
            url_path="analyst-queue",
            default=True,
        ),
        "analyst_investigation": st.Page(
            lambda user=user: analyst.render_investigation(user),
            title="Investigation",
            icon=":material/manage_search:",
            url_path="analyst-investigation",
        ),
        "analyst_playbooks": st.Page(
            lambda user=user: analyst.render_playbooks(user),
            title="Playbooks",
            icon=":material/menu_book:",
            url_path="analyst-playbooks",
        ),
    }


def _build_admin_pages(user: dict[str, object]) -> dict[str, object]:
    return {
        "admin_dashboard": st.Page(
            lambda user=user: admin.render_dashboard(user),
            title="Dashboard",
            icon=":material/space_dashboard:",
            url_path="admin-dashboard",
            default=True,
        ),
        "admin_incident_oversight": st.Page(
            lambda user=user: admin.render_incident_oversight(user),
            title="Incident Oversight",
            icon=":material/monitoring:",
            url_path="admin-incident-oversight",
        ),
    }


def _page_registry_for_user(user: dict[str, object]) -> dict[str, object]:
    role = str(user["role"])
    if role == "Reporter":
        return _build_reporter_pages(user)
    if role == "Analyst":
        return _build_analyst_pages(user)
    return _build_admin_pages(user)


def _render_left_rail(user: dict[str, object], page_registry: dict[str, object], current_page) -> None:
    page_defs = ROLE_PAGE_DEFS[str(user["role"])]

    st.html(
        f"""
        <section class="portal-rail-card">
          <div class="portal-rail-title">{str(user["role"])} Navigation</div>
          <div class="portal-rail-copy">Use the role-specific workspace to move between reporting, triage, and oversight flows.</div>
        </section>
        """
    )

    for page_def in page_defs:
        st.page_link(
            page_registry[page_def["key"]],
            label=page_def["label"],
            icon=page_def["icon"],
            use_container_width=True,
        )

    learn_more_clicked = shell.render_support_card(
        "See something suspicious?",
        "Report it early. Your alert helps the SOC team make better decisions faster.",
        "Learn More",
        key=f"portal-learn-more-{user['role']}",
    )
    if learn_more_clicked:
        target_key = "reporter_faq" if str(user["role"]) == "Reporter" else next(iter(page_registry))
        st.switch_page(page_registry[target_key])

    if st.button("Log Out", use_container_width=True, key="portal-log-out"):
        _clear_session_for_logout()
        st.rerun()


def main() -> None:
    bootstrap_demo_data()
    shell.apply_theme()

    username = st.session_state.get("current_username")
    if not username:
        _render_login(list_demo_users())
        return

    user = login_demo_user(str(username))
    page_registry = _page_registry_for_user(user)
    current_page = st.navigation(list(page_registry.values()), position="hidden")

    shell.render_header(user, notifications=_notification_count(user))
    rail_col, content_col = st.columns([1.02, 4.18], gap="medium")

    with rail_col:
        _render_left_rail(user, page_registry, current_page)

    with content_col:
        current_page.run()


if __name__ == "__main__":
    main()

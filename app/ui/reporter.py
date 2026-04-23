"""Reporter-facing Streamlit screens."""

from __future__ import annotations

from datetime import date, datetime, time
from html import escape
from typing import Any

import streamlit as st

from app.services.intake import create_alert, get_alert, list_alert_types, list_reporter_alerts
from app.ui import shell
from app.ui.components import attachment_metadata, render_reporter_stepper


REPORTER_PAGE_DEFS = [
    {
        "key": "reporter_new_alert",
        "title": "New Alert",
        "icon": ":material/add_circle:",
        "url_path": "reporter-new-alert",
        "default": True,
        "label": "New Alert",
    },
    {
        "key": "reporter_my_alerts",
        "title": "My Alerts",
        "icon": ":material/inbox:",
        "url_path": "reporter-my-alerts",
        "label": "My Alerts",
    },
    {
        "key": "reporter_alert_status",
        "title": "Alert Status",
        "icon": ":material/query_stats:",
        "url_path": "reporter-alert-status",
        "label": "Alert Status",
    },
    {
        "key": "reporter_faq",
        "title": "FAQ / Guidance",
        "icon": ":material/help:",
        "url_path": "reporter-faq",
        "label": "FAQ / Guidance",
    },
    {
        "key": "reporter_contact_soc",
        "title": "Contact SOC",
        "icon": ":material/support_agent:",
        "url_path": "reporter-contact-soc",
        "label": "Contact SOC",
    },
]


WIDGET_KEYS = {
    "alert_type": "reporter_alert_type",
    "severity_estimate": "reporter_severity_estimate",
    "occurred_on": "reporter_occurred_on",
    "occurred_time": "reporter_occurred_time",
    "affected_user": "reporter_affected_user",
    "affected_asset": "reporter_affected_asset",
    "location": "reporter_location",
    "description": "reporter_description",
    "source_ip": "reporter_source_ip",
    "contact_info": "reporter_contact_info",
    "additional_context": "reporter_additional_context",
}


CLOSED_STATUSES = {"Closed", "False Positive"}


def _default_reporter_form(user: dict[str, object]) -> dict[str, object]:
    now = datetime.now().replace(second=0, microsecond=0)
    return {
        "alert_type": list_alert_types()[0],
        "severity_estimate": "Medium",
        "occurred_on": now.date(),
        "occurred_time": now.time(),
        "affected_user": "",
        "affected_asset": "",
        "location": "Melbourne, Australia",
        "description": "",
        "source_ip": "",
        "contact_info": str(user["email"]),
        "additional_context": "",
        "attachments": [],
    }


def _normalize_date(value: object) -> date | None:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str) and value.strip():
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


def _normalize_time(value: object) -> time | None:
    if isinstance(value, time):
        return value.replace(second=0, microsecond=0)
    if isinstance(value, datetime):
        return value.time().replace(second=0, microsecond=0)
    if isinstance(value, str) and value.strip():
        for pattern in ("%H:%M", "%H:%M:%S"):
            try:
                return datetime.strptime(value, pattern).time().replace(second=0, microsecond=0)
            except ValueError:
                continue
    return None


def combine_occurrence_timestamp(occurred_on: object, occurred_time: object) -> str | None:
    """Compose a stable timestamp from date and time inputs."""
    normalized_date = _normalize_date(occurred_on)
    normalized_time = _normalize_time(occurred_time)
    if not normalized_date or not normalized_time:
        return None
    return datetime.combine(normalized_date, normalized_time).isoformat(timespec="minutes")


def validate_reporter_wizard_step(step: int, form: dict[str, object]) -> list[str]:
    """Validate one step of the reporter wizard."""
    errors: list[str] = []

    if step == 1:
        if not str(form.get("alert_type") or "").strip():
            errors.append("Alert type is required.")
        if not str(form.get("severity_estimate") or "").strip():
            errors.append("Estimated severity is required.")
        if not combine_occurrence_timestamp(form.get("occurred_on"), form.get("occurred_time")):
            errors.append("A valid occurrence date and time are required.")
        if not str(form.get("description") or "").strip():
            errors.append("Detailed description is required.")

    if step == 2 and not str(form.get("contact_info") or "").strip():
        errors.append("Contact information is required so the SOC team can follow up.")

    return errors


def _ensure_wizard_state(user: dict[str, object]) -> dict[str, object]:
    state = st.session_state.get("reporter_wizard")
    if not state or state.get("username") != user["username"]:
        state = {
            "username": user["username"],
            "step": 1,
            "completed_steps": [],
            "validation": [],
            "form": _default_reporter_form(user),
            "upload_token": 0,
        }
        st.session_state["reporter_wizard"] = state
        _sync_widgets_from_form(state["form"], force=True)
        return state

    _sync_widgets_from_form(state["form"], force=False)
    return state


def _sync_widgets_from_form(form: dict[str, object], *, force: bool) -> None:
    for field_name, widget_key in WIDGET_KEYS.items():
        if force or widget_key not in st.session_state:
            st.session_state[widget_key] = form.get(field_name)


def _reset_reporter_wizard(user: dict[str, object]) -> None:
    fresh_form = _default_reporter_form(user)
    state = {
        "username": user["username"],
        "step": 1,
        "completed_steps": [],
        "validation": [],
        "form": fresh_form,
        "upload_token": int(st.session_state.get("reporter_wizard", {}).get("upload_token", 0)) + 1,
    }
    st.session_state["reporter_wizard"] = state
    _sync_widgets_from_form(fresh_form, force=True)


def _uploader_key(wizard_state: dict[str, object]) -> str:
    return f"reporter_attachments_{wizard_state['upload_token']}"


def _resolve_attachment_draft(
    uploaded_files: list[Any] | None,
    existing_attachments: list[dict[str, object]] | None,
) -> list[dict[str, object]]:
    uploaded_attachments = attachment_metadata(uploaded_files)
    if uploaded_attachments:
        return uploaded_attachments

    preserved: list[dict[str, object]] = []
    for item in existing_attachments or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        preserved.append(
            {
                "name": name,
                "size": int(item.get("size") or 0),
                "type": str(item.get("type") or "application/octet-stream"),
            }
        )
    return preserved


def _snapshot_wizard_form(wizard_state: dict[str, object]) -> dict[str, object]:
    existing_form = wizard_state.get("form", {})
    form = {
        field_name: st.session_state.get(widget_key, existing_form.get(field_name))
        for field_name, widget_key in WIDGET_KEYS.items()
    }
    form["attachments"] = _resolve_attachment_draft(
        st.session_state.get(_uploader_key(wizard_state)),
        existing_form.get("attachments") if isinstance(existing_form, dict) else None,
    )
    return form


def _record_wizard_form(wizard_state: dict[str, object]) -> dict[str, object]:
    form = _snapshot_wizard_form(wizard_state)
    wizard_state["form"] = form
    return form


def _step_max_available(wizard_state: dict[str, object]) -> int:
    completed = set(wizard_state.get("completed_steps", []))
    if 2 in completed:
        return 3
    if 1 in completed:
        return 2
    return 1


def _status_order_value(status: str) -> int:
    order = {
        "New": 0,
        "In Review": 1,
        "Escalated": 2,
        "Contained": 3,
        "Closed": 4,
        "False Positive": 5,
    }
    return order.get(status, 99)


def _render_validation_errors(wizard_state: dict[str, object]) -> None:
    for error in wizard_state.get("validation", []):
        st.error(error)


def _render_attachment_preview(attachments: list[dict[str, object]]) -> None:
    if not attachments:
        st.caption("No attachment metadata captured yet. Drag-and-drop or browse files to include supporting evidence.")
        return

    rows = "".join(
        f"""
        <article class="portal-alert-row">
          <div class="portal-alert-row-head">
            <div class="portal-alert-id">{escape(str(item['name']))}</div>
            <span class="portal-chip portal-chip--new">{int(item.get('size', 0) / 1024) or 0} KB</span>
          </div>
          <div class="portal-alert-meta">
            <span>{escape(str(item.get('type') or 'application/octet-stream'))}</span>
          </div>
        </article>
        """
        for item in attachments
    )
    st.html(f'<section class="portal-list">{rows}</section>')


def _current_recent_alerts(user: dict[str, object]) -> list[dict[str, object]]:
    return list_reporter_alerts(user)


def _render_right_rail(user: dict[str, object], page_registry: dict[str, object], *, info_text: str) -> None:
    recent_alerts = _current_recent_alerts(user)
    shell.render_info_panel("What happens next?", info_text)
    shell.render_recent_alerts_panel(recent_alerts)
    if st.button("View all alerts", use_container_width=True, key="reporter-view-all-alerts"):
        st.switch_page(page_registry["reporter_my_alerts"])
    shell.render_tips_panel()


def _build_create_payload(user: dict[str, object], form: dict[str, object]) -> dict[str, object]:
    occurred_at = combine_occurrence_timestamp(form.get("occurred_on"), form.get("occurred_time"))
    location = str(form.get("location") or "").strip()
    additional_context = str(form.get("additional_context") or "").strip()

    raw_payload: dict[str, object] = {
        "provider": "Manual Report",
        "event_type": "ManualAlert",
        "event_count": 1,
    }
    if occurred_at:
        raw_payload["reported_occurrence"] = occurred_at
    if location:
        raw_payload["reported_location"] = location
    if additional_context:
        raw_payload["additional_context"] = additional_context

    return {
        "alert_type": str(form.get("alert_type") or "").strip(),
        "severity_estimate": str(form.get("severity_estimate") or "").strip(),
        "description": str(form.get("description") or "").strip(),
        "affected_user": str(form.get("affected_user") or "").strip(),
        "affected_asset": str(form.get("affected_asset") or "").strip(),
        "source_ip": str(form.get("source_ip") or "").strip(),
        "contact_info": str(form.get("contact_info") or user["email"]).strip(),
        "occurred_at": occurred_at,
        "location": location,
        "attachments": form.get("attachments", []),
        "raw_payload": raw_payload,
    }


def _render_step_one(user: dict[str, object], wizard_state: dict[str, object]) -> None:
    with st.container(border=True):
        st.subheader("Alert Details")
        st.caption("Provide the core facts first. Analysts use this to decide what they investigate immediately.")

        alert_types = list(list_alert_types())
        severity_options = ["Low", "Medium", "High", "Critical"]

        top_left, top_middle, top_right = st.columns(3)
        top_left.selectbox(
            "Alert Type *",
            alert_types,
            index=alert_types.index(st.session_state[WIDGET_KEYS["alert_type"]]),
            key=WIDGET_KEYS["alert_type"],
        )
        top_middle.selectbox(
            "Estimated Severity *",
            severity_options,
            index=severity_options.index(st.session_state[WIDGET_KEYS["severity_estimate"]]),
            key=WIDGET_KEYS["severity_estimate"],
        )
        top_right.markdown("**When did this occur?**")
        date_col, time_col = top_right.columns(2)
        date_col.date_input("Date", key=WIDGET_KEYS["occurred_on"], label_visibility="collapsed")
        time_col.time_input("Time", key=WIDGET_KEYS["occurred_time"], label_visibility="collapsed", step=300)

        middle_left, middle_middle, middle_right = st.columns(3)
        middle_left.text_input("Affected User (if known)", key=WIDGET_KEYS["affected_user"], placeholder="jordan.kim@company.com")
        middle_middle.text_input("Affected Asset / System (if known)", key=WIDGET_KEYS["affected_asset"], placeholder="Workstation-45")
        middle_right.text_input("Location", key=WIDGET_KEYS["location"], placeholder="Melbourne, Australia")

        st.text_area(
            "Detailed Description *",
            key=WIDGET_KEYS["description"],
            height=165,
            placeholder="Describe what happened, what you saw, and anything the analyst should review first.",
        )

        st.markdown("**Evidence / Attachments**")
        st.caption("Attachment metadata only is stored in v1. Files are not persisted to disk.")
        st.file_uploader(
            "Upload supporting screenshots, headers, or notes",
            type=["png", "jpg", "jpeg", "pdf", "txt", "eml", "csv", "json", "log"],
            accept_multiple_files=True,
            key=_uploader_key(wizard_state),
            label_visibility="collapsed",
        )
        current_uploads = attachment_metadata(st.session_state.get(_uploader_key(wizard_state)))
        staged_attachments = _resolve_attachment_draft(
            st.session_state.get(_uploader_key(wizard_state)),
            wizard_state.get("form", {}).get("attachments"),
        )
        if staged_attachments and not current_uploads:
            st.caption("Staged attachment metadata is preserved in this draft. Re-upload only if you want to replace it.")
        _render_attachment_preview(staged_attachments)

        cancel_col, spacer_col, next_col = st.columns([1.1, 2.4, 1.6])
        if cancel_col.button("Cancel", use_container_width=True, key="reporter-step1-cancel"):
            st.session_state.pop("reporter_submission_success", None)
            _reset_reporter_wizard(user)
            st.rerun()
        if next_col.button("Next: Additional Information", type="primary", use_container_width=True, key="reporter-step1-next"):
            form = _record_wizard_form(wizard_state)
            validation = validate_reporter_wizard_step(1, form)
            wizard_state["validation"] = validation
            if validation:
                st.rerun()
            wizard_state["completed_steps"] = sorted({*wizard_state.get("completed_steps", []), 1})
            wizard_state["step"] = 2
            st.rerun()


def _render_step_two(user: dict[str, object], wizard_state: dict[str, object]) -> None:
    with st.container(border=True):
        st.subheader("Additional Information")
        st.caption("Optional technical detail helps the SOC team triage faster, but you do not need to know everything.")

        left, right = st.columns(2)
        left.text_input("Source IP (if known)", key=WIDGET_KEYS["source_ip"], placeholder="203.0.113.19")
        right.text_input("Best Contact Method *", key=WIDGET_KEYS["contact_info"], placeholder="name@company.com or phone extension")
        st.text_area(
            "Additional Context",
            key=WIDGET_KEYS["additional_context"],
            height=180,
            placeholder="Example: user did not click the link, saw MFA prompts, or another teammate received the same email.",
        )

        wizard_snapshot = wizard_state.get("form", {})
        shell.render_detail_grid(
            [
                ("Alert Type", str(wizard_snapshot.get("alert_type") or "Not set")),
                ("Severity", str(wizard_snapshot.get("severity_estimate") or "Not set")),
                ("Occurred", shell.format_timestamp(combine_occurrence_timestamp(wizard_snapshot.get("occurred_on"), wizard_snapshot.get("occurred_time")))),
                ("Attachments", str(len(wizard_snapshot.get("attachments", [])))),
            ]
        )

        back_col, spacer_col, next_col = st.columns([1.1, 2.4, 1.6])
        if back_col.button("Back", use_container_width=True, key="reporter-step2-back"):
            wizard_state["validation"] = []
            wizard_state["step"] = 1
            st.rerun()
        if next_col.button("Next: Review & Submit", type="primary", use_container_width=True, key="reporter-step2-next"):
            form = _record_wizard_form(wizard_state)
            validation = validate_reporter_wizard_step(2, form)
            wizard_state["validation"] = validation
            if validation:
                st.rerun()
            wizard_state["completed_steps"] = sorted({*wizard_state.get("completed_steps", []), 1, 2})
            wizard_state["step"] = 3
            st.rerun()


def _render_step_three(user: dict[str, object], wizard_state: dict[str, object], page_registry: dict[str, object]) -> None:
    form = wizard_state.get("form", {})
    with st.container(border=True):
        st.subheader("Review & Submit")
        st.caption("Check the report before sending it into the SOC queue.")

        shell.render_detail_grid(
            [
                ("Alert Type", str(form.get("alert_type") or "Not set")),
                ("Severity", str(form.get("severity_estimate") or "Not set")),
                ("Occurred", shell.format_timestamp(combine_occurrence_timestamp(form.get("occurred_on"), form.get("occurred_time")))),
                ("Affected User", str(form.get("affected_user") or "Unknown user")),
                ("Affected Asset", str(form.get("affected_asset") or "Unknown asset")),
                ("Location", str(form.get("location") or "Not provided")),
                ("Contact Info", str(form.get("contact_info") or user["email"])),
                ("Source IP", str(form.get("source_ip") or "Unknown")),
            ]
        )
        st.markdown("**Detailed Description**")
        st.write(str(form.get("description") or "No description provided."))

        if str(form.get("additional_context") or "").strip():
            st.markdown("**Additional Context**")
            st.write(str(form.get("additional_context")))

        st.markdown("**Attachments**")
        _render_attachment_preview(form.get("attachments", []))

        back_col, spacer_col, submit_col = st.columns([1.1, 2.1, 1.9])
        if back_col.button("Back", use_container_width=True, key="reporter-step3-back"):
            wizard_state["step"] = 2
            st.rerun()
        if submit_col.button("Submit Alert", type="primary", use_container_width=True, key="reporter-step3-submit"):
            validation = validate_reporter_wizard_step(1, form) + validate_reporter_wizard_step(2, form)
            wizard_state["validation"] = validation
            if validation:
                wizard_state["step"] = 1 if validate_reporter_wizard_step(1, form) else 2
                st.rerun()

            created = create_alert(user, _build_create_payload(user, form))
            st.session_state["selected_alert_id"] = created["alert_id"]
            st.session_state["selected_incident_id"] = created["incident_id"]
            st.session_state["reporter_submission_success"] = {
                "alert_id": created["alert_id"],
                "status": created["status"],
            }
            _reset_reporter_wizard(user)
            st.rerun()

    if st.button("Go to My Alerts", use_container_width=False, key="reporter-go-my-alerts"):
        st.switch_page(page_registry["reporter_my_alerts"])


def render_new_alert(user: dict[str, object], page_registry: dict[str, object]) -> None:
    """Render the redesigned reporter alert wizard."""
    wizard_state = _ensure_wizard_state(user)
    shell.render_page_intro(
        "Report a New Alert",
        "Provide as much detail as possible. Our SOC team will investigate and you can track the outcome from My Alerts.",
        eyebrow="Reporter Portal",
    )

    submission = st.session_state.get("reporter_submission_success")
    if submission:
        shell.render_success_banner(str(submission["alert_id"]), str(submission["status"]))

    _render_validation_errors(wizard_state)

    clicked_step = render_reporter_stepper(
        current_step=int(wizard_state["step"]),
        completed_steps=list(wizard_state.get("completed_steps", [])),
        max_available_step=_step_max_available(wizard_state),
    )
    if clicked_step and clicked_step <= _step_max_available(wizard_state):
        wizard_state["step"] = clicked_step
        wizard_state["validation"] = []
        st.rerun()

    main_col, side_col = st.columns([2.35, 1.15], gap="large")
    with main_col:
        if wizard_state["step"] == 1:
            _render_step_one(user, wizard_state)
        elif wizard_state["step"] == 2:
            _render_step_two(user, wizard_state)
        else:
            _render_step_three(user, wizard_state, page_registry)

    with side_col:
        _render_right_rail(
            user,
            page_registry,
            info_text="Your alert will be reviewed by our SOC analysts. You can track status changes from My Alerts.",
        )


def _render_alert_detail(alert: dict[str, object]) -> None:
    shell.render_detail_grid(
        [
            ("Alert ID", str(alert["alert_id"])),
            ("Status", str(alert["status"])),
            ("Priority", str(alert.get("priority") or "Pending")),
            ("Occurred", shell.format_timestamp(alert.get("occurred_at"))),
            ("Location", str(alert.get("location") or "Not provided")),
            ("Assigned Analyst", str(alert.get("assigned_to_name") or "Unassigned")),
            ("Incident ID", str(alert.get("incident_id") or "Pending")),
            ("Attachments", str(alert.get("attachment_count") or 0)),
        ]
    )
    st.markdown("**Description**")
    st.write(str(alert["description"]))
    st.markdown("**Evidence**")
    _render_attachment_preview(alert.get("attachments", []))
    with st.expander("Reporter-visible updates"):
        if alert["notes"]:
            for note in alert["notes"]:
                st.markdown(
                    f"**{note['created_at']} · {note['author_name']}**  \n"
                    f"{note['content']}"
                )
        else:
            st.caption("No reporter-visible notes yet.")
    with st.expander("Raw Payload"):
        st.json(alert["raw_payload"])


def render_my_alerts(user: dict[str, object], page_registry: dict[str, object]) -> None:
    """Render the redesigned reporter alert list and detail page."""
    alerts = list_reporter_alerts(user)
    shell.render_page_intro(
        "My Alerts",
        "Review your submitted alerts, check current status, and see reporter-visible updates from the SOC team.",
        eyebrow="Reporter Portal",
    )

    if not alerts:
        shell.render_info_panel("No alerts yet", "When you submit a report, it will appear here with status, analyst assignment, and visible notes.")
        if st.button("Create a new alert", type="primary", key="reporter-my-alerts-empty"):
            st.switch_page(page_registry["reporter_new_alert"])
        return

    open_alerts = [alert for alert in alerts if alert["status"] not in CLOSED_STATUSES]
    shell.render_stat_grid(
        [
            ("Total Alerts", str(len(alerts))),
            ("Open", str(len(open_alerts))),
            ("Latest Update", shell.format_timestamp(alerts[0]["updated_at"])),
        ]
    )

    main_col, side_col = st.columns([2.25, 1.1], gap="large")
    with main_col:
        st.html(
            f"""
            <section class="portal-side-card portal-side-card--soft">
              <div class="portal-side-title">Submitted Alerts</div>
              <div class="portal-list">
                {''.join(
                    f'''
                    <article class="portal-alert-row">
                      <div class="portal-alert-row-head">
                        <div class="portal-alert-id">{escape(str(alert["alert_id"]))}</div>
                        {shell.status_chip_html(str(alert["status"]))}
                      </div>
                      <div class="portal-alert-title">{escape(str(alert["alert_type"]))}</div>
                      <div class="portal-alert-meta">
                        <span>{escape(shell.format_timestamp(alert.get("updated_at")))}</span>
                        <span>{escape(str(alert.get("location") or "Location not provided"))}</span>
                        <span>{escape(str(alert.get("attachment_count", 0)))} attachment(s)</span>
                      </div>
                    </article>
                    '''
                    for alert in alerts
                )}
              </div>
            </section>
            """
        )

        alert_ids = [alert["alert_id"] for alert in alerts]
        default_id = st.session_state.get("selected_alert_id", alert_ids[0])
        selected_alert_id = st.selectbox(
            "Inspect alert",
            alert_ids,
            index=alert_ids.index(default_id) if default_id in alert_ids else 0,
            format_func=lambda value: next(
                f"{value} · {alert['alert_type']} · {alert['status']}"
                for alert in alerts
                if alert["alert_id"] == value
            ),
        )
        st.session_state["selected_alert_id"] = selected_alert_id
        selected_alert = get_alert(selected_alert_id, user)

        with st.container(border=True):
            st.subheader("Alert Detail")
            _render_alert_detail(selected_alert)

    with side_col:
        shell.render_info_panel("How status updates work", "New and In Review mean the SOC is actively triaging. Closed or False Positive means no further action is needed from you.")
        shell.render_recent_alerts_panel(alerts)
        if st.button("Create another alert", use_container_width=True, key="reporter-create-another"):
            st.switch_page(page_registry["reporter_new_alert"])


def render_alert_status(user: dict[str, object], page_registry: dict[str, object]) -> None:
    """Render a focused reporter view of open alert status."""
    alerts = sorted(list_reporter_alerts(user), key=lambda item: (_status_order_value(item["status"]), item["updated_at"]))
    open_alerts = [alert for alert in alerts if alert["status"] not in CLOSED_STATUSES]

    shell.render_page_intro(
        "Alert Status",
        "See which reports are still active, what stage they are in, and what to expect next.",
        eyebrow="Reporter Portal",
    )
    shell.render_stat_grid(
        [
            ("Open Alerts", str(len(open_alerts))),
            ("Escalated", str(sum(1 for alert in open_alerts if alert["status"] == "Escalated"))),
            ("Contained / Closed", str(sum(1 for alert in alerts if alert["status"] in {"Contained", "Closed"}))),
        ]
    )

    main_col, side_col = st.columns([2.25, 1.1], gap="large")
    with main_col:
        with st.container(border=True):
            st.subheader("Active Reports")
            if not open_alerts:
                st.info("You do not have any open alerts right now.")
            else:
                st.html(
                    f"""
                    <section class="portal-list">
                      {''.join(
                          f'''
                          <article class="portal-alert-row">
                            <div class="portal-alert-row-head">
                              <div class="portal-alert-id">{escape(str(alert["alert_id"]))}</div>
                              {shell.status_chip_html(str(alert["status"]))}
                            </div>
                            <div class="portal-alert-title">{escape(str(alert["alert_type"]))}</div>
                            <div class="portal-alert-meta">
                              <span>{escape(shell.format_timestamp(alert.get("updated_at")))}</span>
                              <span>{escape(str(alert.get("assigned_to_name") or "Awaiting assignment"))}</span>
                            </div>
                          </article>
                          '''
                          for alert in open_alerts
                      )}
                    </section>
                    """
                )

        if open_alerts:
            selected = st.selectbox(
                "Open report detail",
                [alert["alert_id"] for alert in open_alerts],
                format_func=lambda value: next(
                    f"{value} · {alert['alert_type']} · {alert['status']}"
                    for alert in open_alerts
                    if alert["alert_id"] == value
                ),
                key="reporter-open-alert-status-select",
            )
            with st.container(border=True):
                st.subheader("Current Status Detail")
                _render_alert_detail(get_alert(selected, user))

    with side_col:
        shell.render_info_panel("What the statuses mean", "New means received, In Review means triage in progress, Escalated means deeper investigation, and Closed means no further action is needed.")
        shell.render_recent_alerts_panel(alerts, title="Recent Status Changes")
        if st.button("Report something new", type="primary", use_container_width=True, key="reporter-status-new"):
            st.switch_page(page_registry["reporter_new_alert"])


def render_faq_guidance(user: dict[str, object], page_registry: dict[str, object]) -> None:
    """Render lightweight FAQ and reporting guidance."""
    shell.render_page_intro(
        "FAQ / Guidance",
        "Use this page for quick answers on when to report, what to include, and what the SOC team does next.",
        eyebrow="Reporter Portal",
    )

    left, right = st.columns([2, 1], gap="large")
    with left:
        with st.container(border=True):
            st.subheader("When should I report?")
            st.write("Report anything suspicious even if you are not sure it is malicious. The SOC can validate it for you.")
            st.subheader("What helps analysts most?")
            st.write("Clear timing, affected user or device, what you saw, and whether anyone clicked or interacted with the event.")
            st.subheader("Will I get feedback?")
            st.write("Yes. Reporter-visible updates appear in My Alerts when the analyst adds notes that are safe to share.")
        with st.container(border=True):
            st.subheader("Quick Reporting Checklist")
            st.markdown(
                "- Include what happened and when\n"
                "- Mention the user or asset if known\n"
                "- Do not investigate suspicious links yourself\n"
                "- Attach screenshots, headers, or logs if available"
            )
    with right:
        shell.render_tips_panel()
        if st.button("Create a new alert", type="primary", use_container_width=True, key="reporter-faq-new"):
            st.switch_page(page_registry["reporter_new_alert"])


def render_contact_soc(user: dict[str, object], page_registry: dict[str, object]) -> None:
    """Render lightweight SOC contact guidance."""
    shell.render_page_intro(
        "Contact SOC",
        "Reach the security team for urgent follow-up, additional evidence, or status clarification on an existing report.",
        eyebrow="Reporter Portal",
    )

    left, right = st.columns([2, 1], gap="large")
    with left:
        with st.container(border=True):
            st.subheader("SOC Contact Channels")
            shell.render_detail_grid(
                [
                    ("Email", "soc@lighthouse.demo"),
                    ("Hotline", "+61 2 5550 0142"),
                    ("Hours", "24/7 monitoring"),
                    ("Best reference", "Include your Alert ID in the subject or message"),
                ]
            )
            st.markdown("**When to contact us directly**")
            st.write("Use direct contact when you need to add urgent evidence, correct a report, or notify us that a situation is actively worsening.")
        with st.container(border=True):
            st.subheader("Before you reach out")
            st.write("If you already submitted an alert, keep the alert ID nearby so the SOC team can locate your report quickly.")
    with right:
        shell.render_info_panel("Response expectations", "Urgent incidents are triaged first. Non-urgent questions may still be easier to track through My Alerts.")
        if st.button("Open My Alerts", use_container_width=True, key="reporter-contact-my-alerts"):
            st.switch_page(page_registry["reporter_my_alerts"])

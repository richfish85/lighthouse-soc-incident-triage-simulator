"""Shared shell helpers for the Lighthouse SOC UI."""

from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path

import streamlit as st


ROOT_DIR = Path(__file__).resolve().parents[1]
PORTAL_CSS_PATH = ROOT_DIR / "ui" / "portal.css"


ROLE_SUBTITLE = {
    "Reporter": "Reporter Portal",
    "Analyst": "Analyst Workspace",
    "Admin": "SOC Lead Console",
}


def apply_theme() -> None:
    """Inject the shared Lighthouse SOC portal theme."""
    css = PORTAL_CSS_PATH.read_text(encoding="utf-8")
    st.html(f"<style>{css}</style>")


def _initials(full_name: str) -> str:
    parts = [part for part in full_name.split() if part]
    if not parts:
        return "LS"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return f"{parts[0][0]}{parts[-1][0]}".upper()


def format_timestamp(value: str | None) -> str:
    """Render an ISO-like timestamp into a friendlier UI string."""
    if not value:
        return "Not provided"
    try:
        return datetime.fromisoformat(value).strftime("%b %d, %Y • %I:%M %p")
    except ValueError:
        return value


def logo_svg() -> str:
    return """
    <svg width="62" height="62" viewBox="0 0 62 62" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <circle cx="31" cy="31" r="30" fill="#09111E" stroke="rgba(255,255,255,0.42)" stroke-width="1.2"/>
      <path d="M25 46V22l6-7 6 7v24H25Z" fill="#F5F7FA"/>
      <rect x="28.8" y="25.2" width="4.4" height="5.8" fill="#09111E"/>
      <path d="M37 21l14 4-14 4v-8Z" fill="#FFBF1F"/>
      <path d="M12 43c4.8-1.8 8.6-1.8 11.6 0 3.2 1.8 7 1.8 11.2 0 4-1.8 7.8-1.8 11.4 0 1.1.6 2.3 1 3.6 1.3" stroke="#F5F7FA" stroke-width="1.4" stroke-linecap="round"/>
    </svg>
    """


def render_header(user: dict[str, object], notifications: int = 2) -> None:
    """Render the top application header."""
    st.html(
        f"""
        <section class="portal-header">
          <div class="portal-brand">
            {logo_svg()}
            <div class="portal-brand-copy">
              <div class="portal-brand-title">LIGHTHOUSE <span>SOC</span></div>
              <div class="portal-brand-subtitle">{escape(ROLE_SUBTITLE.get(str(user["role"]), "Security Operations"))}</div>
            </div>
          </div>
          <div class="portal-header-actions">
            <div class="portal-action"><span class="portal-badge">{notifications}</span> Notifications</div>
            <div class="portal-action">Need help?</div>
            <div class="portal-user">
              <div class="portal-user-avatar">{escape(_initials(str(user["full_name"])))}</div>
              <div class="portal-user-meta">
                <div class="portal-user-name">{escape(str(user["full_name"]))}</div>
                <div class="portal-user-role">{escape(str(user["role"]))}</div>
              </div>
            </div>
          </div>
        </section>
        """
    )


def render_page_intro(title: str, subtitle: str, eyebrow: str = "Lighthouse SOC") -> None:
    """Render a reusable page heading block."""
    st.html(
        f"""
        <section class="portal-page-head">
          <div class="portal-eyebrow">{escape(eyebrow)}</div>
          <h1 class="portal-page-title">{escape(title)}</h1>
          <div class="portal-page-copy">{escape(subtitle)}</div>
        </section>
        """
    )


def status_chip_html(status: str) -> str:
    """Return a styled badge for a status value."""
    normalized = status.lower().replace(" ", "-")
    return f'<span class="portal-chip portal-chip--{escape(normalized)}">{escape(status)}</span>'


def _render_alert_rows(alerts: list[dict[str, object]], empty_message: str) -> str:
    if not alerts:
        return f'<div class="portal-empty">{escape(empty_message)}</div>'

    rows: list[str] = []
    for alert in alerts:
        rows.append(
            f"""
            <article class="portal-alert-row">
              <div class="portal-alert-row-head">
                <div class="portal-alert-id">{escape(str(alert["alert_id"]))}</div>
                {status_chip_html(str(alert["status"]))}
              </div>
              <div class="portal-alert-title">{escape(str(alert["alert_type"]))}</div>
              <div class="portal-alert-meta">
                <span>{escape(format_timestamp(alert.get("updated_at")))}</span>
                <span>{escape(str(alert.get("location") or "Location not provided"))}</span>
                <span>{escape(str(alert.get("attachment_count", 0)))} attachment(s)</span>
              </div>
            </article>
            """
        )
    return "".join(rows)


def render_recent_alerts_panel(alerts: list[dict[str, object]], title: str = "My Recent Alerts") -> None:
    """Render a compact recent-alerts rail card."""
    st.html(
        f"""
        <section class="portal-side-card portal-side-card--soft">
          <div class="portal-side-title">{escape(title)}</div>
          <div class="portal-list">
            {_render_alert_rows(alerts[:5], "No reporter alerts yet.")}
          </div>
        </section>
        """
    )


def render_info_panel(title: str, body: str) -> None:
    st.html(
        f"""
        <section class="portal-side-card portal-side-card--soft">
          <div class="portal-side-title">{escape(title)}</div>
          <div class="portal-side-copy">{escape(body)}</div>
        </section>
        """
    )


def render_tips_panel() -> None:
    st.html(
        """
        <section class="portal-side-card">
          <div class="portal-side-title">Security Reporting Tips</div>
          <ul class="portal-helper-list">
            <li>When in doubt, report it. A small signal is better than a missed incident.</li>
            <li>Do not click suspicious links or open attachments to investigate them yourself.</li>
            <li>Include as much timing, context, and device detail as you can remember.</li>
            <li>Your report is confidential and will be reviewed by the SOC team.</li>
          </ul>
        </section>
        """
    )


def render_support_card(title: str, copy: str, button_label: str, *, key: str) -> bool:
    st.html(
        f"""
        <section class="portal-rail-card portal-rail-card--soft">
          <div class="portal-rail-title">{escape(title)}</div>
          <div class="portal-rail-copy">{escape(copy)}</div>
        </section>
        """
    )
    return st.button(button_label, use_container_width=True, key=key)


def render_stat_grid(stats: list[tuple[str, str]]) -> None:
    cards = "".join(
        f"""
        <div class="portal-stat">
          <div class="portal-stat-label">{escape(label)}</div>
          <div class="portal-stat-value">{escape(value)}</div>
        </div>
        """
        for label, value in stats
    )
    st.html(f'<section class="portal-stat-grid">{cards}</section>')


def render_detail_grid(items: list[tuple[str, str]]) -> None:
    cells = "".join(
        f"""
        <div class="portal-detail-item">
          <div class="portal-detail-label">{escape(label)}</div>
          <div class="portal-detail-value">{escape(value)}</div>
        </div>
        """
        for label, value in items
    )
    st.html(f'<section class="portal-detail-grid">{cells}</section>')


def render_success_banner(alert_id: str, status: str) -> None:
    st.html(
        f"""
        <section class="portal-success-banner">
          <strong>Alert {escape(alert_id)} created.</strong> The SOC queue now shows this report with status {escape(status)}.
        </section>
        """
    )

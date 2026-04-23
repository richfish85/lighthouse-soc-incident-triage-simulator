"""Small custom UI components for Lighthouse SOC."""

from __future__ import annotations

from typing import Any

import streamlit as st


STEPPER_HTML = """
<div id="reporter-stepper-root"></div>
"""


STEPPER_CSS = """
:host {
  display: block;
}

.stepper {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.85rem;
  margin-bottom: 1rem;
}

.step {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.9rem;
  padding: 0.45rem 0;
}

.step button {
  appearance: none;
  border: none;
  background: transparent;
  color: inherit;
  padding: 0;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  width: 100%;
  text-align: left;
  font-family: inherit;
}

.step button:disabled {
  cursor: default;
}

.step-index {
  width: 2rem;
  height: 2rem;
  border-radius: 999px;
  border: 1px solid rgba(149, 165, 188, 0.34);
  color: rgba(245, 247, 250, 0.92);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(10, 20, 33, 0.75);
  font-weight: 700;
  flex: 0 0 auto;
}

.step-copy {
  display: flex;
  flex-direction: column;
  gap: 0.12rem;
}

.step-title {
  color: rgba(245, 247, 250, 0.95);
  font-weight: 650;
  font-size: 0.98rem;
}

.step-subtitle {
  color: rgba(149, 165, 188, 0.94);
  font-size: 0.84rem;
}

.step.current .step-index,
.step.complete .step-index {
  background: linear-gradient(180deg, #ffd043, #ffbf1f);
  border-color: rgba(255, 208, 67, 0.65);
  color: #07111d;
}

.step.available:hover .step-title {
  color: #ffd56d;
}

@media (max-width: 980px) {
  .stepper {
    grid-template-columns: 1fr;
  }
}
"""


STEPPER_JS = """
export default function(component) {
    const { data, setTriggerValue, parentElement } = component;
    const payload = data || {};
    const steps = payload.steps || [];
    const currentStep = Number(payload.current_step || 1);
    const completedSteps = new Set(payload.completed_steps || []);
    const maxAvailable = Number(payload.max_available_step || 1);

    const root = parentElement.getElementById("reporter-stepper-root");
    root.innerHTML = "";

    const wrapper = document.createElement("div");
    wrapper.className = "stepper";

    steps.forEach((step) => {
        const number = Number(step.number);
        const article = document.createElement("article");
        article.className = "step";

        if (number === currentStep) {
            article.classList.add("current");
        }
        if (completedSteps.has(number)) {
            article.classList.add("complete");
        }
        if (number <= maxAvailable) {
            article.classList.add("available");
        }

        const button = document.createElement("button");
        button.type = "button";
        button.disabled = number > maxAvailable;
        button.innerHTML = `
            <span class="step-index">${number}</span>
            <span class="step-copy">
                <span class="step-title">${step.title}</span>
                <span class="step-subtitle">${step.subtitle || ""}</span>
            </span>
        `;
        button.onclick = () => {
            if (number <= maxAvailable) {
                setTriggerValue("clicked_step", number);
            }
        };

        article.appendChild(button);
        wrapper.appendChild(article);
    });

    root.appendChild(wrapper);
};
"""


_REPORTER_STEPPER = st.components.v2.component(
    "reporter_stepper",
    html=STEPPER_HTML,
    css=STEPPER_CSS,
    js=STEPPER_JS,
)


def render_reporter_stepper(
    *,
    current_step: int,
    completed_steps: list[int],
    max_available_step: int,
    key: str = "reporter-stepper",
) -> int | None:
    """Render the custom stepper and return a clicked step when applicable."""
    result = _REPORTER_STEPPER(
        key=key,
        data={
            "steps": [
                {"number": 1, "title": "Alert Details", "subtitle": "Capture the core incident"},
                {"number": 2, "title": "Additional Information", "subtitle": "Give analysts more context"},
                {"number": 3, "title": "Review & Submit", "subtitle": "Confirm before sending"},
            ],
            "current_step": current_step,
            "completed_steps": completed_steps,
            "max_available_step": max_available_step,
        },
        on_clicked_step_change=lambda: None,
    )
    clicked_step = getattr(result, "clicked_step", None)
    return int(clicked_step) if clicked_step else None


def attachment_metadata(files: list[Any] | None) -> list[dict[str, object]]:
    """Convert Streamlit uploaded files into metadata-only attachment objects."""
    metadata: list[dict[str, object]] = []
    for file in files or []:
        metadata.append(
            {
                "name": getattr(file, "name", "attachment"),
                "size": int(getattr(file, "size", 0) or 0),
                "type": getattr(file, "type", None) or "application/octet-stream",
            }
        )
    return metadata

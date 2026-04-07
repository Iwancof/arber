"""Prompt template registry.

Templates are versioned and stored in code for v1.
Future: move to DB-backed prompt_template table.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PromptTemplate:
    """A versioned prompt template."""
    template_id: str
    version: str
    task_type: str
    description: str


# Registry of available templates
TEMPLATES: dict[str, PromptTemplate] = {
    "event_extract_v1": PromptTemplate(
        template_id="event_extract_v1",
        version="1.0.0",
        task_type="event_extract",
        description=(
            "Extract structured events from "
            "financial documents"
        ),
    ),
    "single_name_forecast_v1": PromptTemplate(
        template_id="single_name_forecast_v1",
        version="1.0.0",
        task_type="single_name_forecast",
        description=(
            "Generate relative performance forecast "
            "for a single instrument"
        ),
    ),
    "skeptic_review_v1": PromptTemplate(
        template_id="skeptic_review_v1",
        version="1.0.0",
        task_type="skeptic_review",
        description=(
            "Adversarial review of a forecast"
        ),
    ),
    "judge_postmortem_v1": PromptTemplate(
        template_id="judge_postmortem_v1",
        version="1.0.0",
        task_type="judge_postmortem",
        description=(
            "Judge forecast accuracy after outcome"
        ),
    ),
}


def get_template(
    task_type: str,
) -> PromptTemplate | None:
    """Get the active template for a task type."""
    for t in TEMPLATES.values():
        if t.task_type == task_type:
            return t
    return None

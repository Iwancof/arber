"""Prompt template loader.

Loads system/user prompts from the prompts/ directory.
Templates use Jinja2 for variable substitution.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import BaseLoader, Environment

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


@dataclass(frozen=True)
class PromptTemplate:
    """A loaded prompt template pair."""
    task_type: str
    version: str
    system_text: str
    user_template: str

    def render_user(self, **kwargs: Any) -> str:
        """Render the user template with variables."""
        env = Environment(
            loader=_StringLoader(self.user_template),
            autoescape=False,
        )
        tmpl = env.get_template("user")
        return tmpl.render(**kwargs)


class _StringLoader(BaseLoader):
    """Jinja2 loader from a string."""

    def __init__(self, source: str) -> None:
        self._source = source

    def get_source(
        self,
        environment: Environment,
        template: str,
    ) -> tuple[str, str | None, Any]:
        return self._source, None, lambda: True


def load_template(
    task_type: str,
    version: str = "v1",
) -> PromptTemplate | None:
    """Load a prompt template from disk.

    Looks for prompts/{version}/{task_type}/system.txt
    and prompts/{version}/{task_type}/user.txt.j2
    """
    base = PROMPTS_DIR / version / task_type
    system_path = base / "system.txt"
    user_path = base / "user.txt.j2"

    if not system_path.exists() or not user_path.exists():
        return None

    return PromptTemplate(
        task_type=task_type,
        version=version,
        system_text=system_path.read_text().strip(),
        user_template=user_path.read_text(),
    )


# Pre-loaded registry for quick access
TEMPLATES: dict[str, PromptTemplate] = {}


def _init_templates() -> None:
    """Load all v1 templates on import."""
    for task_type in [
        "event_extract",
        "single_name_forecast",
        "skeptic_review",
        "judge_postmortem",
    ]:
        tmpl = load_template(task_type)
        if tmpl:
            TEMPLATES[task_type] = tmpl


_init_templates()


def get_template(
    task_type: str,
) -> PromptTemplate | None:
    """Get the active template for a task type."""
    return TEMPLATES.get(task_type)

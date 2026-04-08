"""Prompt template loader.

Loads system/user prompts from the prompts/ directory.
Templates use Jinja2 for variable substitution.

Supports both English (v2) and Japanese (v2_ja) prompt packs.
Japanese templates are stored with a "_ja" suffix in the registry key,
e.g., "event_extract_ja".
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import BaseLoader, Environment, Undefined

PROMPTS_DIR = (
    Path(__file__).resolve().parent.parent.parent / "prompts"
)

# Active prompt versions. Change these to switch all prompts.
ACTIVE_VERSION = "v2"
ACTIVE_VERSION_JA = "v2_ja"


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
            undefined=_SilentUndefined,
        )
        tmpl = env.get_template("user")
        return tmpl.render(**kwargs)


class _SilentUndefined(Undefined):
    """Undefined that renders as empty string."""

    def __str__(self) -> str:
        return ""

    def __iter__(self) -> Any:
        return iter([])

    def __bool__(self) -> bool:
        return False


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
    version: str | None = None,
) -> PromptTemplate | None:
    """Load a prompt template from disk.

    Falls back to v1 if v2 doesn't have the template.
    """
    ver = version or ACTIVE_VERSION
    base = PROMPTS_DIR / ver / task_type
    system_path = base / "system.txt"
    user_path = base / "user.txt.j2"

    if not system_path.exists() or not user_path.exists():
        # Fallback to v1 (only for non-JA versions)
        if ver != "v1" and not ver.endswith("_ja"):
            return load_template(task_type, version="v1")
        return None

    return PromptTemplate(
        task_type=task_type,
        version=ver,
        system_text=system_path.read_text().strip(),
        user_template=user_path.read_text(),
    )


# Pre-loaded registry for quick access
TEMPLATES: dict[str, PromptTemplate] = {}

# All supported task types
_TASK_TYPES = [
    "event_extract",
    "single_name_forecast",
    "skeptic_review",
    "judge_postmortem",
    "noise_classifier",
    "inquiry_question_generator",
]


def _init_templates() -> None:
    """Load all templates on import.

    Loads both English (v2) and Japanese (v2_ja) templates.
    Japanese templates are stored with a "_ja" suffix in the key.
    """
    for task_type in _TASK_TYPES:
        # Load English (v2) templates
        tmpl = load_template(task_type)
        if tmpl:
            TEMPLATES[task_type] = tmpl

        # Load Japanese (v2_ja) templates
        tmpl_ja = load_template(task_type, version=ACTIVE_VERSION_JA)
        if tmpl_ja:
            TEMPLATES[f"{task_type}_ja"] = tmpl_ja


_init_templates()


def get_template(
    task_type: str,
) -> PromptTemplate | None:
    """Get the active template for a task type."""
    return TEMPLATES.get(task_type)


def get_template_for_language(
    task_type: str,
    language: str = "en",
) -> PromptTemplate | None:
    """Get the active template for a task type in the specified language.

    Falls back to English if the requested language is not available.

    Args:
        task_type: The prompt task type (e.g., "event_extract").
        language: Language code ("en" or "ja").

    Returns:
        The matching PromptTemplate, or None if not found.
    """
    if language == "ja":
        return TEMPLATES.get(f"{task_type}_ja") or TEMPLATES.get(task_type)
    return TEMPLATES.get(task_type)

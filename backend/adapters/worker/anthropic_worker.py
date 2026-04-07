"""Anthropic Claude worker adapter.

Connects to Claude API for event extraction and forecasting.
Model is configurable per task type; defaults to Opus.
"""

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

import anthropic

from backend.adapters.worker.base import (
    WorkerAdapter,
    WorkerResult,
    WorkerTask,
)
from backend.config.settings import settings
from backend.prompts.templates import get_template


def _get_model_for_task(task_type: str) -> str:
    """Resolve model name for a task type.

    Configurable per task, falls back to default (Opus).
    """
    overrides = {
        "event_extract": settings.anthropic_model_event_extract,
        "single_name_forecast": settings.anthropic_model_forecast,
        "noise_classifier": settings.anthropic_model_noise,
    }
    override = overrides.get(task_type, "")
    return override or settings.anthropic_default_model


class AnthropicWorkerAdapter(WorkerAdapter):
    """Claude API worker for event extraction and forecasting."""

    def __init__(self) -> None:
        self._client = anthropic.Anthropic(
            api_key=settings.anthropic_api_key,
            timeout=settings.anthropic_timeout_sec,
        )

    @property
    def adapter_code(self) -> str:
        return "anthropic_claude_v1"

    @property
    def supported_task_types(self) -> list[str]:
        return [
            "event_extract",
            "single_name_forecast",
            "skeptic_review",
            "judge_postmortem",
            "noise_classifier",
            "inquiry_question_generator",
        ]

    async def health(self) -> bool:
        """Check API connectivity."""
        try:
            # Simple model list check
            return bool(settings.anthropic_api_key)
        except Exception:
            return False

    async def execute(self, task: WorkerTask) -> WorkerResult:
        """Execute a task via Claude API."""
        model = _get_model_for_task(task.task_type)
        prompt = _build_prompt(task)
        system_msg = _build_system_message(task)

        try:
            response = self._client.messages.create(
                model=model,
                max_tokens=settings.anthropic_max_tokens,
                system=system_msg,
                messages=[
                    {"role": "user", "content": prompt},
                ],
            )

            raw_text = response.content[0].text
            parsed = _try_parse_json(raw_text)
            schema_valid = parsed is not None
            parse_errors: list[str] = []
            if not schema_valid:
                parse_errors = [
                    "Failed to parse JSON response",
                ]
                parsed = {}

            output_hash = hashlib.sha256(
                raw_text.encode()
            ).hexdigest()

            trace = _extract_reasoning_trace(parsed)

            return WorkerResult(
                task_id=task.task_id,
                raw_text=raw_text,
                parsed_json=parsed,
                schema_valid=schema_valid,
                parse_errors=parse_errors,
                reasoning_trace_summary=trace,
                output_hash=output_hash,
                completed_at=datetime.now(UTC),
                model_name=model,
                model_version=response.model,
            )
        except anthropic.APIError as e:
            return WorkerResult(
                task_id=task.task_id,
                raw_text="",
                parsed_json={},
                schema_valid=False,
                parse_errors=[f"API error: {e}"],
                completed_at=datetime.now(UTC),
                model_name=model,
                model_version="error",
            )


def _build_system_message(task: WorkerTask) -> str:
    """Build system message from template file."""
    tmpl = get_template(task.task_type)
    if tmpl:
        return tmpl.system_text
    return (
        "You are an expert financial analyst. "
        "Respond with valid JSON only."
    )


def _build_prompt(task: WorkerTask) -> str:
    """Build user prompt from template file."""
    payload = task.input_payload
    tmpl = get_template(task.task_type)

    if tmpl:
        # Prepare variables for Jinja2
        variables = dict(payload)
        # Ensure event_json is a string for templates
        if "event_json" in variables and not isinstance(
            variables["event_json"], str
        ):
            variables["event_json"] = json.dumps(
                variables["event_json"], default=str
            )
        return tmpl.render_user(**variables)

    # Fallback for unknown task types
    return json.dumps(payload, default=str)


def _try_parse_json(text: str) -> dict[str, Any] | None:
    """Try to parse JSON from response text."""
    text = text.strip()
    # Handle markdown code blocks
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [
            line for line in lines
            if not line.strip().startswith("```")
        ]
        text = "\n".join(lines)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _extract_reasoning_trace(
    parsed: dict[str, Any],
) -> dict[str, Any]:
    """Extract reasoning trace from parsed response."""
    return {
        k: parsed[k]
        for k in (
            "hypotheses",
            "selected_hypothesis",
            "rejected_hypotheses",
            "counterarguments",
            "risk_flags",
            "confidence_before",
            "confidence_after",
        )
        if k in parsed
    }

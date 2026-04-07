"""OpenAI GPT worker adapter.

Connects to OpenAI API for event extraction and forecasting.
Uses the same prompt templates as Anthropic adapter.
"""

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

import openai

from backend.adapters.worker.base import (
    WorkerAdapter,
    WorkerResult,
    WorkerTask,
)
from backend.config.settings import settings
from backend.prompts.templates import get_template


def _get_model_for_task(task_type: str) -> str:
    """Resolve model for a task type."""
    overrides = {
        "event_extract": (
            settings.openai_model_event_extract
        ),
        "single_name_forecast": (
            settings.openai_model_forecast
        ),
        "noise_classifier": (
            settings.openai_model_noise
        ),
    }
    override = overrides.get(task_type, "")
    return override or settings.openai_default_model


class OpenAIWorkerAdapter(WorkerAdapter):
    """OpenAI GPT worker adapter."""

    def __init__(self) -> None:
        self._client = openai.OpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.openai_timeout_sec,
        )

    @property
    def adapter_code(self) -> str:
        return "openai_gpt_v1"

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
        return bool(settings.openai_api_key)

    async def execute(
        self, task: WorkerTask
    ) -> WorkerResult:
        """Execute a task via OpenAI API."""
        model = _get_model_for_task(task.task_type)
        system_msg = _build_system(task)
        user_msg = _build_prompt(task)

        try:
            response = self._client.chat.completions.create(
                model=model,
                max_tokens=settings.openai_max_tokens,
                messages=[
                    {
                        "role": "system",
                        "content": system_msg,
                    },
                    {
                        "role": "user",
                        "content": user_msg,
                    },
                ],
                temperature=0.2,
            )

            raw_text = (
                response.choices[0].message.content
                or ""
            )
            parsed = _try_parse_json(raw_text)
            schema_valid = parsed is not None
            parse_errors: list[str] = []
            if not schema_valid:
                parse_errors = [
                    "Failed to parse JSON response"
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
                model_version=response.model or model,
            )
        except openai.APIError as e:
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


def _build_system(task: WorkerTask) -> str:
    """Build system message from template."""
    tmpl = get_template(task.task_type)
    if tmpl:
        return tmpl.system_text
    return (
        "You are an expert financial analyst. "
        "Respond with valid JSON only."
    )


def _build_prompt(task: WorkerTask) -> str:
    """Build user prompt from template."""
    payload = task.input_payload
    tmpl = get_template(task.task_type)

    if tmpl:
        variables = dict(payload)
        if "event_json" in variables and not isinstance(
            variables["event_json"], str
        ):
            variables["event_json"] = json.dumps(
                variables["event_json"], default=str
            )
        return tmpl.render_user(**variables)

    return json.dumps(payload, default=str)


def _try_parse_json(
    text: str,
) -> dict[str, Any] | None:
    """Try to parse JSON from response."""
    text = text.strip()
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

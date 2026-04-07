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


def _get_model_for_task(task_type: str) -> str:
    """Resolve model name for a task type.

    Configurable per task, falls back to default (Opus).
    """
    overrides = {
        "event_extract": settings.anthropic_model_event_extract,
        "single_name_forecast": settings.anthropic_model_forecast,
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
    """Build system message based on task type."""
    base = (
        "You are an expert financial analyst for "
        "Event Intelligence OS. "
        "Always respond with valid JSON only. "
        "No markdown, no explanation outside JSON."
    )

    if task.task_type == "event_extract":
        return (
            f"{base}\n"
            "Extract structured events from the "
            "document. "
            "Output must match the event_record schema."
        )
    if task.task_type == "single_name_forecast":
        return (
            f"{base}\n"
            "Generate a forecast for the given "
            "instrument based on the event.\n"
            "You MUST use EXACTLY the JSON schema "
            "shown in the user message.\n"
            "Every field listed is REQUIRED.\n"
            "Do NOT invent your own field names.\n"
            "Do NOT add fields not in the schema.\n"
            "Focus on relative performance vs "
            "benchmark, never point price."
        )
    return base


def _build_prompt(task: WorkerTask) -> str:
    """Build the user prompt from task input."""
    payload = task.input_payload

    if task.task_type == "event_extract":
        headline = payload.get("headline", "")
        text = payload.get("raw_text", "")
        return (
            "Extract structured events from this "
            "document.\n\n"
            f"Headline: {headline}\n"
            f"Content: {text}\n\n"
            "Respond with JSON:\n"
            "{\n"
            '  "schema_name": "event_record",\n'
            '  "schema_version": "1.0.0",\n'
            '  "events": [\n'
            "    {\n"
            '      "event_type": "<type>",\n'
            '      "affected_assets": ["<symbol>"],\n'
            '      "direction_hint": '
            '"positive|negative|neutral|mixed",\n'
            '      "materiality": <0.0-1.0>,\n'
            '      "novelty": <0.0-1.0>,\n'
            '      "evidence_spans": [\n'
            '        {"text": "<quote>", '
            '"start": <int>, "end": <int>}\n'
            "      ]\n"
            "    }\n"
            "  ]\n"
            "}"
        )

    if task.task_type == "single_name_forecast":
        symbol = payload.get("instrument_symbol", "")
        event_type = payload.get("event_type", "")
        event_json = payload.get("event_json", {})
        direction = payload.get(
            "direction_hint", "unknown"
        )
        ej = json.dumps(event_json, default=str)
        return (
            f"Forecast for {symbol} based on this "
            f"event.\n\n"
            f"Event type: {event_type}\n"
            f"Direction hint: {direction}\n"
            f"Event data: {ej}\n\n"
            "Respond with EXACTLY this JSON structure "
            "(fill in real values):\n\n"
            "```json\n"
            "{\n"
            '  "hypotheses": [\n'
            "    {\n"
            '      "code": "hypothesis_name",\n'
            '      "weight": 0.6,\n'
            '      "description": "why this matters"\n'
            "    }\n"
            "  ],\n"
            '  "selected_hypothesis": '
            '"hypothesis_name",\n'
            '  "rejected_hypotheses": '
            '["other_hypothesis"],\n'
            '  "counterarguments": [\n'
            "    {\n"
            '      "code": "risk_name",\n'
            '      "severity": "medium"\n'
            "    }\n"
            "  ],\n"
            '  "risk_flags": [],\n'
            '  "evidence_refs": [],\n'
            '  "confidence_before": 0.5,\n'
            '  "confidence_after": 0.65,\n'
            '  "direction_hint": "positive",\n'
            '  "horizons": {\n'
            '    "1d": {\n'
            '      "p_outperform": 0.58,\n'
            '      "p_underperform": 0.42,\n'
            '      "ret_q10": -0.015,\n'
            '      "ret_q50": 0.005,\n'
            '      "ret_q90": 0.025\n'
            "    },\n"
            '    "5d": {\n'
            '      "p_outperform": 0.55,\n'
            '      "p_underperform": 0.45,\n'
            '      "ret_q10": -0.03,\n'
            '      "ret_q50": 0.008,\n'
            '      "ret_q90": 0.04\n'
            "    }\n"
            "  }\n"
            "}\n"
            "```\n\n"
            "RULES:\n"
            "- Use ONLY these exact field names\n"
            "- hypotheses: at least 2\n"
            "- horizons: must include 1d and 5d\n"
            "- All numbers must be actual values\n"
            "- p_outperform + p_underperform = 1.0\n"
            "- confidence_after between 0 and 1\n"
            "- Return raw JSON only, no markdown"
        )

    # Generic fallback
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

"""Claude Code CLI worker adapter.

Uses `claude -p --output-format json` for LLM execution.
Claude Code uses the user's subscription (no API key needed).
"""

import asyncio
import hashlib
import json
import logging
from datetime import UTC, datetime
from typing import Any

from backend.adapters.worker.base import (
    WorkerAdapter,
    WorkerResult,
    WorkerTask,
)
from backend.prompts.templates import get_template

logger = logging.getLogger("eos.claude_code_worker")


class ClaudeCodeWorkerAdapter(WorkerAdapter):
    """Claude Code CLI worker."""

    @property
    def adapter_code(self) -> str:
        return "claude_code_v1"

    @property
    def supported_task_types(self) -> list[str]:
        return [
            "event_extract",
            "single_name_forecast",
            "skeptic_review",
            "judge_postmortem",
            "noise_classifier",
            "inquiry_question_generator",
            "event_extract_ja",
            "noise_classifier_ja",
            "single_name_forecast_ja",
        ]

    async def health(self) -> bool:
        """Check if claude CLI is available."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "claude", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.wait()
            return proc.returncode == 0
        except Exception:
            return False

    async def execute(
        self, task: WorkerTask
    ) -> WorkerResult:
        """Execute task via claude -p."""
        system_msg = _build_system(task)
        user_msg = _build_prompt(task)

        prompt = (
            f"{system_msg}\n\n---\n\n{user_msg}"
        )

        try:
            raw_text = await _run_claude(
                prompt, timeout=task.timeout_sec
            )
        except Exception as e:
            return WorkerResult(
                task_id=task.task_id,
                raw_text="",
                parsed_json={},
                schema_valid=False,
                parse_errors=[
                    f"Claude Code error: {e}"
                ],
                completed_at=datetime.now(UTC),
                model_name="claude-code",
                model_version="cli",
            )

        parsed = _try_parse_json(raw_text)
        schema_valid = parsed is not None
        parse_errors: list[str] = []
        if not schema_valid:
            parse_errors = [
                "Failed to parse JSON from claude"
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
            model_name="claude-code",
            model_version="cli",
        )


async def _run_claude(
    prompt: str,
    timeout: int = 120,
) -> str:
    """Run claude -p and extract result."""
    proc = await asyncio.create_subprocess_exec(
        "claude", "-p", prompt,
        "--output-format", "json",
        "--tools", "",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=timeout,
        )
    except TimeoutError as exc:
        proc.kill()
        raise TimeoutError(
            f"Claude Code timed out after {timeout}s"
        ) from exc

    if proc.returncode != 0:
        err = (
            stderr.decode()[:200] if stderr else "?"
        )
        raise RuntimeError(
            f"Claude Code exit {proc.returncode}: "
            f"{err}"
        )

    # Parse JSON output
    output = stdout.decode()
    try:
        data = json.loads(output)
    except json.JSONDecodeError:
        # Maybe plain text
        return output.strip()

    # Extract result from claude output format
    result_text = data.get("result", "")
    if result_text:
        return result_text

    return output.strip()


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
        if "event_json" in variables and (
            not isinstance(
                variables["event_json"], str
            )
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
    """Extract reasoning trace from response."""
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

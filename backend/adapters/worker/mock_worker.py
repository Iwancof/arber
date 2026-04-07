"""Mock worker adapter for replay and testing.

Returns deterministic forecast results based on input event data,
enabling replay mode and test execution without external LLM calls.
"""

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from backend.adapters.worker.base import WorkerAdapter, WorkerResult, WorkerTask


class MockWorkerAdapter(WorkerAdapter):
    """Deterministic mock worker for replay/shadow modes."""

    async def health(self) -> bool:
        return True

    @property
    def adapter_code(self) -> str:
        return "mock_deterministic_v1"

    @property
    def supported_task_types(self) -> list[str]:
        return ["event_forecast", "event_extraction", "event_verification"]

    async def execute(self, task: WorkerTask) -> WorkerResult:
        """Generate deterministic forecast based on input hash."""
        input_hash = hashlib.sha256(
            json.dumps(task.input_payload, sort_keys=True, default=str).encode()
        ).hexdigest()

        # Derive deterministic values from hash
        seed = int(input_hash[:8], 16)
        confidence = round(0.3 + (seed % 50) / 100, 4)
        p_outperform = round(0.3 + (seed % 40) / 100, 4)

        direction = "positive" if seed % 3 != 0 else "negative"

        parsed: dict[str, Any] = {
            "schema_name": "forecast",
            "schema_version": "1.0.0",
            "hypotheses": [
                {
                    "code": "event_driven_momentum",
                    "weight": round(confidence, 4),
                    "description": "Event suggests directional momentum",
                },
                {
                    "code": "mean_reversion",
                    "weight": round(1 - confidence, 4),
                    "description": "Historical mean reversion expected",
                },
            ],
            "selected_hypothesis": "event_driven_momentum"
            if confidence > 0.5
            else "mean_reversion",
            "rejected_hypotheses": ["mean_reversion"]
            if confidence > 0.5
            else ["event_driven_momentum"],
            "counterarguments": [
                {"code": "low_sample", "severity": "medium"},
            ],
            "risk_flags": [],
            "evidence_refs": task.evidence_refs,
            "confidence_before": round(confidence - 0.1, 4),
            "confidence_after": confidence,
            "direction_hint": direction,
            "horizons": {
                "1d": {
                    "p_outperform": p_outperform,
                    "p_underperform": round(1 - p_outperform, 4),
                    "ret_q10": round(-0.02 + (seed % 10) / 1000, 8),
                    "ret_q50": round(0.005 + (seed % 20) / 1000, 8),
                    "ret_q90": round(0.03 + (seed % 15) / 1000, 8),
                },
                "5d": {
                    "p_outperform": round(p_outperform * 0.9, 4),
                    "p_underperform": round(1 - p_outperform * 0.9, 4),
                    "ret_q10": round(-0.04 + (seed % 10) / 500, 8),
                    "ret_q50": round(0.01 + (seed % 20) / 500, 8),
                    "ret_q90": round(0.06 + (seed % 15) / 500, 8),
                },
            },
        }

        return WorkerResult(
            task_id=task.task_id,
            raw_text=json.dumps(parsed),
            parsed_json=parsed,
            schema_valid=True,
            reasoning_trace_summary={
                "hypotheses": parsed["hypotheses"],
                "selected_hypothesis": parsed["selected_hypothesis"],
                "confidence_after": parsed["confidence_after"],
            },
            output_hash=input_hash,
            completed_at=datetime.now(tz=UTC),
            model_name="mock_deterministic",
            model_version="1.0.0",
        )

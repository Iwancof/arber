"""Tests for Phase 3 Pydantic schemas."""

from datetime import UTC, datetime
from uuid import uuid4

from backend.schemas.feedback import OutcomeRead, PostmortemRead
from backend.schemas.prompts import (
    PromptResponseCreate,
    PromptTaskCreate,
    PromptTaskRead,
)


def test_prompt_task_create_defaults():
    """PromptTaskCreate should have correct defaults."""
    task = PromptTaskCreate(
        decision_id=uuid4(),
        task_type="pretrade_review",
        prompt_text="Review this event",
        deadline_at=datetime.now(tz=UTC),
    )
    assert task.prompt_template_id == "default_review_v1"
    assert task.prompt_version == "1.0.0"
    assert task.evidence_bundle_json == []


def test_prompt_response_create():
    """PromptResponseCreate should validate."""
    resp = PromptResponseCreate(
        model_name_user_entered="gpt-4",
        raw_response='{"action": "buy"}',
        parsed_json={"action": "buy"},
    )
    assert resp.submitted_by is None
    assert resp.parsed_json is not None


def test_prompt_task_read():
    """PromptTaskRead should parse from dict."""
    now = datetime.now(tz=UTC)
    data = {
        "prompt_task_id": uuid4(),
        "decision_id": uuid4(),
        "task_type": "pretrade_review",
        "prompt_template_id": "default_review_v1",
        "prompt_version": "1.0.0",
        "prompt_text": "Review this event",
        "prompt_schema_name": "prompt_task",
        "prompt_schema_version": "1.0.0",
        "evidence_bundle_json": [],
        "deadline_at": now,
        "status": "created",
        "created_at": now,
    }
    task = PromptTaskRead(**data)
    assert task.status == "created"


def test_outcome_read():
    """OutcomeRead should handle decimals."""
    from decimal import Decimal

    o = OutcomeRead(
        outcome_id=uuid4(),
        forecast_id=uuid4(),
        horizon_code="1d",
        computed_at=datetime.now(tz=UTC),
        realized_rel_return=Decimal("0.025"),
        outcome_json={"source": "market_data"},
    )
    assert o.horizon_code == "1d"


def test_postmortem_read():
    """PostmortemRead should parse correctly."""
    pm = PostmortemRead(
        postmortem_id=uuid4(),
        forecast_id=uuid4(),
        verdict="correct",
        failure_codes_json=[],
        requires_source_review=False,
        requires_prompt_review=False,
        judge_version="v1_simple",
        postmortem_json={},
        created_at=datetime.now(tz=UTC),
    )
    assert pm.verdict == "correct"
    assert pm.requires_source_review is False

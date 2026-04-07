"""Prompt task and response schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from backend.schemas.common import OrmBase, PaginatedResponse


class PromptTaskRead(OrmBase):
    """Prompt task response schema."""

    prompt_task_id: UUID
    decision_id: UUID
    task_type: str
    prompt_template_id: str
    prompt_version: str
    prompt_text: str
    prompt_schema_name: str
    prompt_schema_version: str
    evidence_bundle_json: list[Any]
    deadline_at: datetime
    status: str
    created_by: UUID | None = None
    created_at: datetime


class PromptTaskCreate(OrmBase):
    """Prompt task creation schema."""

    decision_id: UUID
    task_type: str
    prompt_template_id: str = "default_review_v1"
    prompt_version: str = "1.0.0"
    prompt_text: str
    prompt_schema_name: str = "prompt_task"
    prompt_schema_version: str = "1.0.0"
    evidence_bundle_json: list[Any] = []
    deadline_at: datetime
    created_by: UUID | None = None


class PromptTaskList(PaginatedResponse):
    """Paginated list of prompt tasks."""

    items: list[PromptTaskRead]


class PromptResponseRead(OrmBase):
    """Prompt response schema."""

    prompt_response_id: UUID
    prompt_task_id: UUID
    submitted_by: UUID | None = None
    model_name_user_entered: str
    submitted_at: datetime
    raw_response: str
    parsed_json: dict[str, Any] | None = None
    schema_valid: bool
    accepted_for_scoring: bool
    final_weight: float | None = None
    parser_version: str | None = None


class PromptResponseCreate(OrmBase):
    """Prompt response submission schema."""

    model_name_user_entered: str
    raw_response: str
    parsed_json: dict[str, Any] | None = None
    submitted_by: UUID | None = None

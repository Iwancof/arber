"""Prompt task and response API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import get_db
from backend.models.forecasting import (
    PromptResponse,
    PromptTask,
)
from backend.schemas.prompts import (
    PromptResponseCreate,
    PromptResponseRead,
    PromptTaskCreate,
    PromptTaskList,
    PromptTaskRead,
)
from backend.services.prompt_bridge import (
    create_prompt_task,
    submit_response,
    transition_task_status,
)

router = APIRouter(tags=["prompts"])


@router.get(
    "/prompt-tasks",
    response_model=PromptTaskList,
)
async def list_prompt_tasks(
    status: str | None = Query(default=None),
    task_type: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> PromptTaskList:
    """List prompt tasks with optional filters."""
    stmt = select(PromptTask)
    count_stmt = select(func.count()).select_from(
        PromptTask,
    )

    if status:
        stmt = stmt.where(
            PromptTask.status == status,
        )
        count_stmt = count_stmt.where(
            PromptTask.status == status,
        )
    if task_type:
        stmt = stmt.where(
            PromptTask.task_type == task_type,
        )
        count_stmt = count_stmt.where(
            PromptTask.task_type == task_type,
        )

    total = (await db.execute(count_stmt)).scalar_one()
    result = await db.execute(
        stmt.offset(offset)
        .limit(limit)
        .order_by(PromptTask.deadline_at)
    )
    items = [
        PromptTaskRead.model_validate(r)
        for r in result.scalars().all()
    ]
    return PromptTaskList(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/prompt-tasks/{task_id}",
    response_model=PromptTaskRead,
)
async def get_prompt_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> PromptTaskRead:
    """Get a single prompt task by ID."""
    result = await db.execute(
        select(PromptTask).where(
            PromptTask.prompt_task_id == task_id,
        )
    )
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Prompt task not found",
        )
    return PromptTaskRead.model_validate(task)


@router.post(
    "/prompt-tasks",
    response_model=PromptTaskRead,
    status_code=202,
)
async def create_task(
    body: PromptTaskCreate,
    db: AsyncSession = Depends(get_db),
) -> PromptTaskRead:
    """Create a new prompt task for manual review."""
    task = await create_prompt_task(
        db, **body.model_dump()
    )
    return PromptTaskRead.model_validate(task)


@router.post(
    "/prompt-tasks/{task_id}/make-visible",
    response_model=PromptTaskRead,
)
async def make_visible(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> PromptTaskRead:
    """Transition a task from created to visible."""
    try:
        task = await transition_task_status(
            db,
            prompt_task_id=task_id,
            new_status="visible",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=409, detail=str(e),
        ) from e
    return PromptTaskRead.model_validate(task)


@router.post(
    "/prompt-tasks/{task_id}/responses",
    response_model=PromptResponseRead,
    status_code=202,
)
async def submit_task_response(
    task_id: UUID,
    body: PromptResponseCreate,
    db: AsyncSession = Depends(get_db),
) -> PromptResponseRead:
    """Submit a response to a prompt task."""
    try:
        response = await submit_response(
            db,
            prompt_task_id=task_id,
            model_name=body.model_name_user_entered,
            raw_response=body.raw_response,
            parsed_json=body.parsed_json,
            submitted_by=body.submitted_by,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=409, detail=str(e),
        ) from e
    return PromptResponseRead.model_validate(response)


@router.get(
    "/prompt-tasks/{task_id}/responses",
    response_model=list[PromptResponseRead],
)
async def list_task_responses(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[PromptResponseRead]:
    """List all responses for a prompt task."""
    result = await db.execute(
        select(PromptResponse)
        .where(
            PromptResponse.prompt_task_id == task_id,
        )
        .order_by(PromptResponse.submitted_at.desc())
    )
    return [
        PromptResponseRead.model_validate(r)
        for r in result.scalars().all()
    ]

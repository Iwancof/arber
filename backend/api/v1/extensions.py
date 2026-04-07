"""Extension registry API endpoints.

Plugin, schema, feature flag, event type, and contract
compatibility management.
"""


from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import get_db
from backend.models.extensions import (
    ContractCompatibility,
    EventTypeRegistry,
    FeatureFlag,
    PluginRegistry,
    SchemaRegistryEntry,
)
from backend.schemas.extensions import (
    ContractCompatibilityCreate,
    ContractCompatibilityRead,
    EventTypeRegistryCreate,
    EventTypeRegistryRead,
    FeatureFlagCreate,
    FeatureFlagList,
    FeatureFlagRead,
    FeatureFlagUpdate,
    PluginRegistryCreate,
    PluginRegistryList,
    PluginRegistryRead,
    SchemaRegistryCreate,
    SchemaRegistryList,
    SchemaRegistryRead,
)

router = APIRouter(tags=["extensions"])


# === Feature Flags ===

@router.get(
    "/feature-flags",
    response_model=FeatureFlagList,
)
async def list_feature_flags(
    rollout_state: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> FeatureFlagList:
    stmt = select(FeatureFlag)
    count_stmt = select(
        func.count()
    ).select_from(FeatureFlag)
    if rollout_state:
        stmt = stmt.where(
            FeatureFlag.rollout_state == rollout_state
        )
        count_stmt = count_stmt.where(
            FeatureFlag.rollout_state == rollout_state
        )
    total = (await db.execute(count_stmt)).scalar_one()
    result = await db.execute(
        stmt.offset(offset)
        .limit(limit)
        .order_by(FeatureFlag.flag_code)
    )
    items = [
        FeatureFlagRead.model_validate(r)
        for r in result.scalars().all()
    ]
    return FeatureFlagList(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/feature-flags",
    response_model=FeatureFlagRead,
    status_code=201,
)
async def create_feature_flag(
    body: FeatureFlagCreate,
    db: AsyncSession = Depends(get_db),
) -> FeatureFlagRead:
    flag = FeatureFlag(**body.model_dump())
    db.add(flag)
    await db.commit()
    await db.refresh(flag)
    return FeatureFlagRead.model_validate(flag)


@router.patch(
    "/feature-flags/{flag_code}",
    response_model=FeatureFlagRead,
)
async def update_feature_flag(
    flag_code: str,
    body: FeatureFlagUpdate,
    db: AsyncSession = Depends(get_db),
) -> FeatureFlagRead:
    result = await db.execute(
        select(FeatureFlag).where(
            FeatureFlag.flag_code == flag_code
        )
    )
    flag = result.scalar_one_or_none()
    if flag is None:
        raise HTTPException(
            status_code=404,
            detail="Feature flag not found",
        )
    updates = body.model_dump(exclude_unset=True)
    for k, v in updates.items():
        setattr(flag, k, v)
    await db.commit()
    await db.refresh(flag)
    return FeatureFlagRead.model_validate(flag)


# === Schema Registry ===

@router.get(
    "/schema-registry",
    response_model=SchemaRegistryList,
)
async def list_schema_registry(
    schema_name: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> SchemaRegistryList:
    stmt = select(SchemaRegistryEntry)
    count_stmt = select(
        func.count()
    ).select_from(SchemaRegistryEntry)
    if schema_name:
        stmt = stmt.where(
            SchemaRegistryEntry.schema_name
            == schema_name
        )
        count_stmt = count_stmt.where(
            SchemaRegistryEntry.schema_name
            == schema_name
        )
    if status:
        stmt = stmt.where(
            SchemaRegistryEntry.status == status
        )
        count_stmt = count_stmt.where(
            SchemaRegistryEntry.status == status
        )
    total = (await db.execute(count_stmt)).scalar_one()
    result = await db.execute(
        stmt.offset(offset)
        .limit(limit)
        .order_by(
            SchemaRegistryEntry.schema_name,
            SchemaRegistryEntry.semantic_version,
        )
    )
    items = [
        SchemaRegistryRead.model_validate(r)
        for r in result.scalars().all()
    ]
    return SchemaRegistryList(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/schema-registry",
    response_model=SchemaRegistryRead,
    status_code=201,
)
async def create_schema_entry(
    body: SchemaRegistryCreate,
    db: AsyncSession = Depends(get_db),
) -> SchemaRegistryRead:
    entry = SchemaRegistryEntry(**body.model_dump())
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return SchemaRegistryRead.model_validate(entry)


# === Plugins ===

@router.get(
    "/plugins",
    response_model=PluginRegistryList,
)
async def list_plugins(
    plugin_type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> PluginRegistryList:
    stmt = select(PluginRegistry)
    count_stmt = select(
        func.count()
    ).select_from(PluginRegistry)
    if plugin_type:
        stmt = stmt.where(
            PluginRegistry.plugin_type == plugin_type
        )
        count_stmt = count_stmt.where(
            PluginRegistry.plugin_type == plugin_type
        )
    if status:
        stmt = stmt.where(
            PluginRegistry.status == status
        )
        count_stmt = count_stmt.where(
            PluginRegistry.status == status
        )
    total = (await db.execute(count_stmt)).scalar_one()
    result = await db.execute(
        stmt.offset(offset)
        .limit(limit)
        .order_by(PluginRegistry.plugin_code)
    )
    items = [
        PluginRegistryRead.model_validate(r)
        for r in result.scalars().all()
    ]
    return PluginRegistryList(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/plugins",
    response_model=PluginRegistryRead,
    status_code=201,
)
async def create_plugin(
    body: PluginRegistryCreate,
    db: AsyncSession = Depends(get_db),
) -> PluginRegistryRead:
    plugin = PluginRegistry(**body.model_dump())
    db.add(plugin)
    await db.commit()
    await db.refresh(plugin)
    return PluginRegistryRead.model_validate(plugin)


@router.post(
    "/plugins/{plugin_code}/enable",
    response_model=PluginRegistryRead,
)
async def enable_plugin(
    plugin_code: str,
    db: AsyncSession = Depends(get_db),
) -> PluginRegistryRead:
    result = await db.execute(
        select(PluginRegistry).where(
            PluginRegistry.plugin_code == plugin_code
        )
    )
    plugin = result.scalar_one_or_none()
    if plugin is None:
        raise HTTPException(
            status_code=404,
            detail="Plugin not found",
        )
    plugin.status = "enabled"
    await db.commit()
    await db.refresh(plugin)
    return PluginRegistryRead.model_validate(plugin)


@router.post(
    "/plugins/{plugin_code}/disable",
    response_model=PluginRegistryRead,
)
async def disable_plugin(
    plugin_code: str,
    db: AsyncSession = Depends(get_db),
) -> PluginRegistryRead:
    result = await db.execute(
        select(PluginRegistry).where(
            PluginRegistry.plugin_code == plugin_code
        )
    )
    plugin = result.scalar_one_or_none()
    if plugin is None:
        raise HTTPException(
            status_code=404,
            detail="Plugin not found",
        )
    plugin.status = "disabled"
    await db.commit()
    await db.refresh(plugin)
    return PluginRegistryRead.model_validate(plugin)


# === Event Types ===

@router.get(
    "/event-types",
    response_model=list[EventTypeRegistryRead],
)
async def list_event_types(
    status: str | None = Query(default=None),
    event_family: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[EventTypeRegistryRead]:
    stmt = select(EventTypeRegistry)
    if status:
        stmt = stmt.where(
            EventTypeRegistry.status == status
        )
    if event_family:
        stmt = stmt.where(
            EventTypeRegistry.event_family
            == event_family
        )
    result = await db.execute(
        stmt.order_by(
            EventTypeRegistry.event_type_code
        )
    )
    return [
        EventTypeRegistryRead.model_validate(r)
        for r in result.scalars().all()
    ]


@router.post(
    "/event-types",
    response_model=EventTypeRegistryRead,
    status_code=201,
)
async def create_event_type(
    body: EventTypeRegistryCreate,
    db: AsyncSession = Depends(get_db),
) -> EventTypeRegistryRead:
    et = EventTypeRegistry(**body.model_dump())
    db.add(et)
    await db.commit()
    await db.refresh(et)
    return EventTypeRegistryRead.model_validate(et)


# === Contract Compatibility ===

@router.get(
    "/contracts",
    response_model=list[ContractCompatibilityRead],
)
async def list_contracts(
    schema_name: str | None = Query(default=None),
    status: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[ContractCompatibilityRead]:
    stmt = select(ContractCompatibility)
    if schema_name:
        stmt = stmt.where(
            ContractCompatibility.schema_name
            == schema_name
        )
    if status:
        stmt = stmt.where(
            ContractCompatibility.status == status
        )
    result = await db.execute(stmt)
    return [
        ContractCompatibilityRead.model_validate(r)
        for r in result.scalars().all()
    ]


@router.post(
    "/contracts",
    response_model=ContractCompatibilityRead,
    status_code=201,
)
async def create_contract(
    body: ContractCompatibilityCreate,
    db: AsyncSession = Depends(get_db),
) -> ContractCompatibilityRead:
    cc = ContractCompatibility(**body.model_dump())
    db.add(cc)
    await db.commit()
    await db.refresh(cc)
    return ContractCompatibilityRead.model_validate(cc)

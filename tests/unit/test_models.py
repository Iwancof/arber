"""Tests for SQLAlchemy model definitions."""

from backend.models import Base


def test_all_models_registered():
    """All expected tables should be registered in the metadata."""
    table_names = set(Base.metadata.tables.keys())
    # Core tables
    assert "core.market_profile" in table_names
    assert "core.instrument" in table_names
    assert "core.app_user" in table_names
    assert "core.role" in table_names
    # Sources tables
    assert "sources.source_registry" in table_names
    assert "sources.source_endpoint" in table_names
    assert "sources.source_bundle" in table_names
    assert "sources.watch_plan" in table_names
    # Content tables
    assert "content.raw_document" in table_names
    assert "content.event_ledger" in table_names
    assert "content.dedup_cluster" in table_names
    # Forecasting tables
    assert "forecasting.forecast_ledger" in table_names
    assert "forecasting.decision_ledger" in table_names
    assert "forecasting.prompt_task" in table_names
    # Execution tables
    assert "execution.order_ledger" in table_names
    assert "execution.execution_fill" in table_names
    # Feedback tables
    assert "feedback.outcome_ledger" in table_names
    assert "feedback.postmortem_ledger" in table_names
    # Ops tables
    assert "ops.audit_log" in table_names
    assert "ops.kill_switch" in table_names
    assert "ops.watcher_instance" in table_names
    assert "ops.outbox_event" in table_names
    # Extension tables
    assert "core.feature_flag" in table_names
    assert "core.schema_registry" in table_names
    assert "core.event_type_registry" in table_names


def test_table_count():
    """Should have 54 tables across all schemas."""
    assert len(Base.metadata.tables) == 54


def test_ledger_tables_exist():
    """All 7 ledger/content tables must be separate."""
    table_names = set(Base.metadata.tables.keys())
    ledger_tables = {
        "content.raw_document",
        "content.event_ledger",
        "forecasting.forecast_ledger",
        "forecasting.decision_ledger",
        "execution.order_ledger",
        "feedback.outcome_ledger",
        "feedback.postmortem_ledger",
    }
    assert ledger_tables.issubset(table_names)


def test_schema_namespaces():
    """Tables should be distributed across 7 schemas."""
    schemas = {name.split(".")[0] for name in Base.metadata.tables}
    expected = {"core", "sources", "content", "forecasting", "execution", "feedback", "ops"}
    assert expected.issubset(schemas)

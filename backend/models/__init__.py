"""SQLAlchemy ORM models for Event Intelligence OS."""

from backend.models.base import Base
from backend.models.content import (
    DedupCluster,
    DocumentAssetLink,
    EventAssetImpact,
    EventEvidenceLink,
    EventLedger,
    RawDocument,
)
from backend.models.core import (
    AppUser,
    BenchmarkMap,
    Instrument,
    InstrumentAlias,
    MarketProfile,
    Role,
    TradingVenue,
    UserRole,
)
from backend.models.execution import ExecutionFill, OrderLedger, PositionSnapshot
from backend.models.extensions import (
    BrokerAdapterRegistry,
    ContractCompatibility,
    EventTypeRegistry,
    FeatureFlag,
    PluginRegistry,
    ReasonCodeRegistry,
    SchemaRegistryEntry,
    WorkerAdapterRegistry,
)
from backend.models.feedback import (
    ManualModelReliability,
    OutcomeLedger,
    PostmortemLedger,
    ReliabilityStat,
)
from backend.models.forecasting import (
    DecisionLedger,
    DecisionReason,
    ForecastHorizon,
    ForecastLedger,
    PolicyPackRegistry,
    PromptResponse,
    PromptTask,
    ReasoningTrace,
    RetrievalItem,
    RetrievalSet,
)
from backend.models.inquiry import (
    InquiryAssignment,
    InquiryCase,
    InquiryMetricSnapshot,
    InquiryPresence,
    InquiryResolution,
    InquiryResponse,
    InquirySignal,
    InquiryTask,
)
from backend.models.ops import (
    AuditLog,
    JobRun,
    KillSwitch,
    OutboxEvent,
    SystemConfig,
    WatcherInstance,
)
from backend.models.sources import (
    SourceBundle,
    SourceBundleItem,
    SourceCandidate,
    SourceEndpoint,
    SourceRegistry,
    UniverseMember,
    UniverseSet,
    WatchPlan,
    WatchPlanItem,
)

__all__ = [
    "Base",
    # core
    "AppUser", "Role", "UserRole", "MarketProfile", "TradingVenue",
    "Instrument", "InstrumentAlias", "BenchmarkMap",
    # sources
    "SourceRegistry", "SourceEndpoint", "SourceBundle", "SourceBundleItem",
    "SourceCandidate", "UniverseSet", "UniverseMember", "WatchPlan", "WatchPlanItem",
    # content
    "DedupCluster", "RawDocument", "DocumentAssetLink",
    "EventLedger", "EventAssetImpact", "EventEvidenceLink",
    # forecasting
    "RetrievalSet", "RetrievalItem", "ReasoningTrace",
    "ForecastLedger", "ForecastHorizon", "DecisionLedger", "DecisionReason",
    "PromptTask", "PromptResponse", "PolicyPackRegistry",
    # execution
    "OrderLedger", "ExecutionFill", "PositionSnapshot",
    # feedback
    "OutcomeLedger", "PostmortemLedger", "ReliabilityStat", "ManualModelReliability",
    # ops
    "WatcherInstance", "AuditLog", "KillSwitch", "SystemConfig", "JobRun", "OutboxEvent",
    # extensions
    "FeatureFlag", "SchemaRegistryEntry", "EventTypeRegistry", "ReasonCodeRegistry",
    "PluginRegistry", "WorkerAdapterRegistry", "BrokerAdapterRegistry", "ContractCompatibility",
    # inquiry (human_ops)
    "InquiryCase", "InquirySignal", "InquiryTask",
    "InquiryAssignment", "InquiryPresence",
    "InquiryResponse", "InquiryResolution",
    "InquiryMetricSnapshot",
]

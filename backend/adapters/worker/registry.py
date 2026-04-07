"""Worker adapter registry.

Returns the appropriate worker adapter based on
the configured LLM provider.
"""

from backend.adapters.worker.base import WorkerAdapter
from backend.config.settings import settings


def get_worker_adapter() -> WorkerAdapter:
    """Get worker adapter for the configured provider.

    Configured via EOS_LLM_PROVIDER env var:
    - "anthropic" (default) → Claude API
    - "openai" → OpenAI GPT API
    - "mock" → MockWorkerAdapter (testing)
    """
    provider = settings.llm_provider.lower()

    if provider == "openai":
        from backend.adapters.worker.openai_worker import (
            OpenAIWorkerAdapter,
        )
        return OpenAIWorkerAdapter()

    if provider == "mock":
        from backend.adapters.worker.mock_worker import (
            MockWorkerAdapter,
        )
        return MockWorkerAdapter()

    # Default: anthropic
    from backend.adapters.worker.anthropic_worker import (
        AnthropicWorkerAdapter,
    )
    return AnthropicWorkerAdapter()

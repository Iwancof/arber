"""FastAPI middleware for trace context and request logging."""

import time
import uuid

from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.requests import Request
from starlette.responses import Response

from backend.core.trace import TraceContext, set_trace


class TraceMiddleware(BaseHTTPMiddleware):
    """Inject trace context into every request."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Extract or generate trace_id
        trace_id = request.headers.get(
            "X-Trace-ID", uuid.uuid4().hex
        )
        correlation_id = request.headers.get(
            "X-Correlation-ID"
        )

        ctx = TraceContext(
            trace_id=trace_id,
            correlation_id=correlation_id or trace_id,
        )
        set_trace(ctx)

        start = time.monotonic()
        response = await call_next(request)
        duration_ms = (time.monotonic() - start) * 1000

        # Add trace headers to response
        response.headers["X-Trace-ID"] = trace_id
        response.headers["X-Duration-Ms"] = f"{duration_ms:.1f}"

        return response

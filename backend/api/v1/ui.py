"""Web UI pages served by FastAPI."""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["ui"])

_TEMPLATES = Path(__file__).resolve().parent.parent.parent / "templates"


@router.get("/ui/inquiry", response_class=HTMLResponse)
async def inquiry_console() -> HTMLResponse:
    """Inquiry answer console UI."""
    html = (_TEMPLATES / "inquiry.html").read_text()
    return HTMLResponse(content=html)

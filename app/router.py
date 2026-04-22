from pathlib import Path

from fastapi import APIRouter, Header, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.models import RouteRequest, RouteResponse
from app.services import process_route_request

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def demo_home(request: Request):
    """Serve the browser demo; API clients can still call POST /route directly."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"page_title": "Voice-shaped support routing"},
    )


@router.post("/route", response_model=RouteResponse)
def route_support(
    payload: RouteRequest,
    request: Request,
    x_request_id: str | None = Header(default=None, alias="x-request-id"),
):
    """Route a transcript-shaped utterance to a workflow and return structured guidance."""
    cid = x_request_id or getattr(request.state, "correlation_id", None)
    return process_route_request(payload, correlation_id=cid)

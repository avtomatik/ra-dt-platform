from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from .templates import templates

router = APIRouter(tags=["home"])


@router.get("/", response_class=HTMLResponse, name="landing_page")
def landing_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request, name="index.html", context={}
    )

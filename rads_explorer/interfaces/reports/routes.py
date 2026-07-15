from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape

from rads_explorer.config.paths import TEMPLATE_DIR
from rads_explorer.container.container import get_container

jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
    cache_size=0,
)

router = APIRouter(prefix="/reports", tags=["REPORTS"])


@router.get("/certificates", response_class=HTMLResponse)
def certificates(request: Request):
    container = get_container()
    report_service = container.report_service()

    rows = report_service.build_certificates_inventory()

    template = jinja_env.get_template("certificates.html")
    html = template.render(request=request, certificate_report_rows=rows)
    return HTMLResponse(content=html)

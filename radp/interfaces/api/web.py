from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape

from radp.application.reporting.models import CertificateReportFilters
from radp.bootstrap.container import Container
from radp.bootstrap.runtime import get_container
from radp.config.paths import TEMPLATE_DIR

router = APIRouter(prefix="/web", tags=["web"])
jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
    cache_size=0,
)


@router.get("", response_class=HTMLResponse)
def home(request: Request, runtime: Container = Depends(get_container)):
    """Render the local PostgreSQL inventory; do not call the upstream RA."""
    filters = CertificateReportFilters()
    items = runtime.reporting.project_first(filters=filters)
    template = jinja_env.get_template("certificates.html")
    html = template.render(
        request=request,
        certificate_report_rows=items,
        columns=runtime.reporting.columns,
        selected_status="ALL",
        gid=None,
    )
    return HTMLResponse(content=html)

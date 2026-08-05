from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse, HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape

from radp.bootstrap.runtime import get_runtime
from radp.config.paths import TEMPLATE_DIR
from radp.runtime import Runtime

router = APIRouter(prefix="/export", tags=["export"])

jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
    cache_size=0,
)


@router.get("/preview", response_class=HTMLResponse)
def preview(request: Request, runtime: Runtime = Depends(get_runtime)):
    items = runtime.reporting.project_first()
    template = jinja_env.get_template("certificates.html")
    html = template.render(request=request, certificate_report_rows=items)
    return HTMLResponse(content=html)


@router.get("/certificates")
def export_certificates(runtime: Runtime = Depends(get_runtime)):
    report = runtime.reporting.export_excel()
    return FileResponse(report.path, filename=report.path.name)

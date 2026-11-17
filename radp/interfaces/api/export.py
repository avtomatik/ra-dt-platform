from datetime import date

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import FileResponse, HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape

from radp.application.reporting.enums import CertificateReportStatus
from radp.application.reporting.models import CertificateReportFilters
from radp.bootstrap.container import Container
from radp.bootstrap.runtime import get_container
from radp.config.paths import TEMPLATE_DIR

router = APIRouter(prefix="/export", tags=["export"])
jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
    cache_size=0,
)


def _filters(
    status: CertificateReportStatus,
    gid: str | None,
    as_of_date: date | None,
) -> CertificateReportFilters:
    return CertificateReportFilters(
        status=status, gid=gid, as_of_date=as_of_date
    )


@router.get("/preview", response_class=HTMLResponse)
def preview(
    request: Request,
    status: CertificateReportStatus = Query(CertificateReportStatus.ALL),
    gid: str | None = Query(default=None),
    as_of_date: date | None = Query(default=None),
    runtime: Container = Depends(get_container),
):
    filters = _filters(status, gid, as_of_date)
    items = runtime.reporting.project_first(filters=filters)
    template = jinja_env.get_template("certificates.html")
    html = template.render(
        request=request,
        certificate_report_rows=items,
        columns=runtime.reporting.columns,
        selected_status=status.value,
        gid=gid,
    )
    return HTMLResponse(content=html)


@router.get("/certificates")
def export_certificates(
    status: CertificateReportStatus = Query(CertificateReportStatus.ALL),
    gid: str | None = Query(default=None),
    as_of_date: date | None = Query(default=None),
    runtime: Container = Depends(get_container),
):
    report = runtime.reporting.export_excel(_filters(status, gid, as_of_date))
    return FileResponse(
        report.path,
        filename=report.path.name,
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    )

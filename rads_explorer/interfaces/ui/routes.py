from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape

from rads_explorer.config.paths import TEMPLATE_DIR
from rads_explorer.container.container import get_container

jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
    cache_size=0,
)


router = APIRouter()


@router.get("/ui", response_class=HTMLResponse)
def home(num_items: int = 20):
    container = get_container()
    report_service = container.report_service()

    rows = report_service.build_certificates_inventory()

    html = """
    <html>
        <head><title>RADS Explorer</title></head>
        <body>
            <h1>Certificates</h1>
            <ul>
    """

    for c in rows[:num_items]:
        html += f"<li>{c.serial_number} - {c.common_name}</li>"

    html += """
            </ul>
        </body>
    </html>
    """

    return html


@router.get("/ui/certificates", response_class=HTMLResponse)
def certificates(request: Request):
    container = get_container()
    report_service = container.report_service()

    rows = report_service.build_certificates_inventory()

    template = jinja_env.get_template("certificates.html")
    html = template.render(request=request, certificate_report_rows=rows)
    return HTMLResponse(content=html)


@router.get("/ui/reports/expiring", response_class=HTMLResponse)
def expiring(request: Request, days: int = 30):
    container = get_container()
    report_service = container.report_service()

    report = report_service.expiring_certificates_report(days)

    template = jinja_env.get_template("report_expiring.html")
    html = template.render(request=request, report=report)
    return HTMLResponse(content=html)


@router.get("/ui/reports/inventory")
def inventory_report():
    container = get_container()
    report_service = container.report_service()

    report = report_service.certificates_inventory_report()
    output = Path("/tmp/certificates_inventory.xlsx")

    container.xlsx_exporter.export(report, output)
    return FileResponse(output, filename="certificates_inventory.xlsx")

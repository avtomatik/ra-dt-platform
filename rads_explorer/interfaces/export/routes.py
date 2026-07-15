from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import FileResponse

from rads_explorer.config.paths import EXPORTS_DIR
from rads_explorer.container.container import get_container

router = APIRouter(prefix="/export", tags=["EXPORT"])


@router.get("/inventory")
def export_certificates_inventory():
    container = get_container()
    report_service = container.report_service()

    report = report_service.certificates_inventory_report()
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    file_name = f"certificates_inventory_{datetime.now():%Y-%m-%d-%H-%M}.xlsx"
    output = EXPORTS_DIR / file_name

    container.exporter().export(report, output)
    return FileResponse(output, filename=file_name)

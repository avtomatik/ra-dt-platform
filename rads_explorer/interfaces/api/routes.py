from fastapi import APIRouter

from rads_explorer.config.paths import EXPORTS_DIR
from rads_explorer.container.container import get_container

router = APIRouter()


@router.get("/health")
def health():
    container = get_container()
    settings = container._settings
    return {
        "status": "ok",
        "transport": settings.transport,
        "api_base_url": str(settings.api_base_url),
        "curl_path": str(settings.curl_path),
        "cert_thumbprint_set": bool(settings.cert_thumbprint),
    }


@router.get("/debug/config")
def debug_config():
    container = get_container()
    settings = container._settings
    return {
        "env": settings.env,
        "transport": settings.transport,
        "api_base_url": str(settings.api_base_url),
        "api_version": settings.api_version,
        "timeout": settings.timeout,
        "verify_tls": settings.verify_tls,
        "debug_http": settings.debug_http,
        "curl_path": str(settings.curl_path),
        "cert_thumbprint": settings.cert_thumbprint[:8] + "...",
    }


@router.get("/debug/transport")
def debug_transport():
    container = get_container()
    t = container._transport
    return {
        "type": type(t).__name__,
        "api_base_url": str(container._settings.api_base_url),
    }


@router.get("/certificates")
def certificates():
    container = get_container()
    service = container.certificate_service()
    return service.list().model_dump(by_alias=True)


@router.get("/certificates/serialNumber/{serial_number}")
def get_certificate_by_serial(serial_number: str):
    container = get_container()
    service = container.certificate_service()
    return service.detail_by_serial(serial_number)


@router.get("/certificates/{certificate_id}")
def get_certificate_by_id(certificate_id: str):
    container = get_container()
    service = container.certificate_service()
    return service.detail_by_id(certificate_id)


@router.get("/users")
def users():
    container = get_container()
    service = container.user_service()
    return service.list_users().model_dump(by_alias=True)


@router.get("/certRequests")
def cert_requests():
    container = get_container()
    service = container.cert_request_service()
    return service.list_requests().model_dump(by_alias=True)


@router.get("/search/certificates")
def search_certificates(q: str):
    container = get_container()
    service = container.certificate_service()
    return service.search(q)


@router.get("/reports/expiring")
def expiring(days: int = 30):
    container = get_container()
    report_service = container.report_service()
    return report_service.expiring_certificates_report(days).data


@router.get("/reports/certificates-inventory")
def certificates_inventory():
    container = get_container()
    report_service = container.report_service()
    return report_service.build_certificates_inventory()


@router.get("/export/expiring.xlsx")
def export_expiring(days: int = 30):
    container = get_container()
    report_service = container.report_service()
    report = report_service.expiring_certificates_report(days)
    path = EXPORTS_DIR / "expiring.xlsx"
    container.exporter().export(report, path)
    return {"file": str(path)}


@router.get("/export/certificates-inventory.xlsx")
def export_certificates_inventory():
    container = get_container()
    report_service = container.report_service()
    report = report_service.certificates_inventory_report()
    path = EXPORTS_DIR / "certificates-inventory.xlsx"
    container.exporter().export(report, path)
    return {"file": str(path)}

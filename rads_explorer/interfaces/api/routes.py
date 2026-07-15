from fastapi import APIRouter

from rads_explorer.container.container import get_container

router = APIRouter(prefix="/api/ra", tags=["API"])


@router.get("/certificates")
def certificates():
    container = get_container()
    service = container.certificate_service()
    return service.list_page().model_dump(by_alias=True)


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

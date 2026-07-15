from fastapi import APIRouter

from rads_explorer.container.container import get_container

router = APIRouter(prefix="/health", tags=["HEALTH"])


@router.get("")
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

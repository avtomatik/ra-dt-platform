from fastapi import APIRouter

from rads_explorer.container.container import get_container

router = APIRouter(prefix="/debug", tags=["DEBUG"])


@router.get("/config")
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


@router.get("/transport")
def debug_transport():
    container = get_container()
    t = container._transport
    return {
        "type": type(t).__name__,
        "api_base_url": str(container._settings.api_base_url),
    }

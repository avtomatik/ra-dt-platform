from fastapi import APIRouter, Depends

from radp.bootstrap.container import Container
from radp.bootstrap.runtime import get_container

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/config")
def config(runtime: Container = Depends(get_container)):
    settings = runtime.settings
    return {
        "transport_mode": settings.transport.mode.value,
        "api_base_url": str(settings.remote_ra.base_url),
        "curl_path": str(settings.transport.curl_path),
        "database": settings.database.database,
    }


@router.get("/transport")
def transport(runtime: Container = Depends(get_container)):
    return {"type": type(runtime.transport).__name__}

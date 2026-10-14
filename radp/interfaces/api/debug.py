from fastapi import APIRouter, Depends

from radp.bootstrap.runtime import get_runtime
from radp.runtime import Runtime

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/config")
def config(runtime: Runtime = Depends(get_runtime)):
    settings = runtime.settings
    return {
        "transport_mode": settings.transport.mode,
        "api_base_url": str(settings.remote_ra.base_url),
        "curl_path": str(settings.transport.curl_path),
        "database": settings.database.name,
    }


@router.get("/transport")
def transport(runtime: Runtime = Depends(get_runtime)):
    return {"type": type(runtime.transport).__name__}

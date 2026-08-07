from fastapi import APIRouter, Depends

from radp.bootstrap.runtime import get_runtime
from radp.runtime import Runtime

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/config")
def config(runtime: Runtime = Depends(get_runtime)):
    settings = runtime.settings
    return {
        "transport": settings.transport,
        "api_base_url": str(settings.api_base_url),
        "curl_path": str(settings.curl_path),
        "cert_thumbprint": settings.cert_thumbprint[:8] + "...",
        "database": settings.database_name,
    }


@router.get("/transport")
def transport(runtime: Runtime = Depends(get_runtime)):
    return {"type": type(runtime.transport).__name__}

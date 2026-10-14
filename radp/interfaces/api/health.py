from fastapi import APIRouter, Depends

from radp.bootstrap.runtime import get_runtime
from radp.runtime import Runtime

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health(runtime: Runtime = Depends(get_runtime)):
    settings = runtime.settings
    tables = runtime.database.list_tables()
    return {
        "status": "ok",
        "transport_mode": settings.transport.mode,
        "api_base_url": str(settings.remote_ra.base_url),
        "curl_path": str(settings.transport.curl_path),
        "cert_thumbprint_set": bool(settings.transport.cert_thumbprint),
        "database": settings.database.driver,
        "database_tables": tables,
    }

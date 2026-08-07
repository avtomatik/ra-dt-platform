from fastapi import APIRouter, Depends

from radp.bootstrap.runtime import get_runtime
from radp.runtime import Runtime

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/certificates/sync")
async def synchronize(runtime: Runtime = Depends(get_runtime)):
    count = await runtime.synchronization.synchronize()
    return {"synchronized": count}

from fastapi import APIRouter, Depends

from radp.bootstrap.container import Container
from radp.bootstrap.runtime import get_container

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/certificates/sync")
async def synchronize(runtime: Container = Depends(get_container)):
    count = await runtime.synchronization.run()
    return {"synchronized": count}

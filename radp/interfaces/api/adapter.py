from fastapi import APIRouter, Depends

from radp.bootstrap.runtime import get_runtime
from radp.runtime import Runtime

router = APIRouter(prefix="/adapter", tags=["adapter"])


@router.get("/certificates")
async def list_first_page(runtime: Runtime = Depends(get_runtime)):
    page = await runtime.client.list_first_page()
    return page.model_dump(by_alias=True)


@router.get("/certificates/{certificate_id}")
async def get_certificate(
    certificate_id: str, runtime: Runtime = Depends(get_runtime)
):
    certificate = await runtime.client.get_certificate(certificate_id)
    return certificate


@router.get("/certificates/search")
async def search_certificates(q: str, runtime: Runtime = Depends(get_runtime)):
    certificates = await runtime.client.search_certificates(q)
    return certificates

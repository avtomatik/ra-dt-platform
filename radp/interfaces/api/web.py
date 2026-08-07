from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from radp.bootstrap.runtime import get_runtime
from radp.runtime import Runtime

router = APIRouter(prefix="/web", tags=["web"])


@router.get("", response_class=HTMLResponse)
async def home(runtime: Runtime = Depends(get_runtime)):
    page = await runtime.client.list_first_page()
    page_items = page.items

    html = f"""
    <html>
        <head><title>RADP Platform</title></head>
        <body>
            <h1>Перечень первых {len(page_items)} сертификатов</h1>
            <ul>
    """

    for item in page_items:
        html += f"<li>{item.id} ({item.serial_number}): {item.name_attributes.get('commonName')}</li>"

    html += """
            </ul>
        </body>
    </html>
    """

    return html

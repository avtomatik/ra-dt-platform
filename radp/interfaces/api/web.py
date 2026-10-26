from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from radp.bootstrap.container import Container
from radp.bootstrap.runtime import get_container

router = APIRouter(prefix="/web", tags=["web"])


@router.get("", response_class=HTMLResponse)
async def home(runtime: Container = Depends(get_container)):
    page = await runtime.client.list_first_summary_page()
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

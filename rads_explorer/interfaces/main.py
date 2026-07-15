from fastapi import FastAPI

from rads_explorer.interfaces.api.routes import router as api_router
from rads_explorer.interfaces.debug.routes import router as debug_router
from rads_explorer.interfaces.export.routes import router as export_router
from rads_explorer.interfaces.health.routes import router as health_router
from rads_explorer.interfaces.reports.routes import router as reports_router
from rads_explorer.interfaces.ui.routes import router as ui_router

app = FastAPI(title="Registration Authority Data Services Enterprise API")

app.include_router(api_router)
app.include_router(debug_router)
app.include_router(export_router)
app.include_router(health_router)
app.include_router(reports_router)
app.include_router(ui_router)

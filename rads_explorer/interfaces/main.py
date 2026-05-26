from fastapi import FastAPI

from rads_explorer.interfaces.api.routes import router as api_router
from rads_explorer.interfaces.ui.routes import router as ui_router

app = FastAPI(title="Registration Authority Data Services Enterprise API")

app.include_router(api_router, prefix="/api/ra")
app.include_router(ui_router)

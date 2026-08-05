from fastapi import FastAPI

from .adapter import router as adapter_router
from .admin import router as admin_router
from .debug import router as debug_router
from .export import router as export_router
from .health import router as health_router
from .web import router as web_router


def create_app() -> FastAPI:
    app = FastAPI(title="Registration Authority Data Platform")

    app.include_router(adapter_router)
    app.include_router(admin_router)
    app.include_router(debug_router)
    app.include_router(export_router)
    app.include_router(health_router)
    app.include_router(web_router)

    return app


app = create_app()

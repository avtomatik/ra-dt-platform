import uvicorn


def serve(host: str = "127.0.0.1", port: int = 8000):
    uvicorn.run(
        "radp.interfaces.api.main:app", host=host, port=port, reload=False
    )

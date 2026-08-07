import uvicorn


def serve(args) -> None:
    uvicorn.run(
        "radp.interfaces.api.main:app",
        host=args.host,
        port=args.port,
        reload=False,
    )

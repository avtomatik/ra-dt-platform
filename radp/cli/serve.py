import argparse

import uvicorn


def serve(args: argparse.Namespace) -> None:
    uvicorn.run("radp.interfaces.api.main:app", host=args.host, port=args.port)

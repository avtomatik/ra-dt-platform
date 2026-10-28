import argparse
import asyncio
import logging

from radp.application.doctor.service import CheckResult
from radp.bootstrap.runtime import get_container
from radp.config.settings import Settings

logger = logging.getLogger(__name__)


def doctor(_args: argparse.Namespace) -> int:
    try:
        Settings()
    except Exception as exc:
        logger.error("configuration: FAIL - %s", exc)
        return 1
    logger.info("configuration: OK - settings loaded")
    try:
        runtime = get_container()
        results = asyncio.run(runtime.doctor.run())
    except Exception as exc:
        logger.error("runtime: FAIL - %s", exc)
        return 1
    for result in results:
        _log_result(result)
    return 0 if all(result.ok for result in results) else 1


def _log_result(result: CheckResult) -> None:
    state = "OK" if result.ok else "FAIL"
    logger.info("%s: %s - %s", result.name, state, result.message)

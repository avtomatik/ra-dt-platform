import argparse
import logging

from radp.bootstrap.runtime import get_runtime

logger = logging.getLogger(__name__)


def excel(_args: argparse.Namespace) -> None:
    report = get_runtime().reporting.export_excel()
    logger.info("Exported %s to %s", report.name, report.path)

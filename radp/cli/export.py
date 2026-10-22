import argparse
import logging

from radp.bootstrap.runtime import get_container
from radp.config.paths import EXPORTS_DIR

logger = logging.getLogger(__name__)


def excel(_args: argparse.Namespace) -> None:
    report = get_container().reporting.export_excel()
    logger.info("Exported %s to %s", report.name, report.path)


def flush(_args: argparse.Namespace) -> None:
    """Remove generated XLSX files on explicit operator request only."""
    removed = 0
    if not EXPORTS_DIR.exists():
        logger.info(
            "Export directory %s does not exist; nothing to flush.",
            EXPORTS_DIR,
        )
        return
    if not EXPORTS_DIR.is_dir():
        raise NotADirectoryError(
            f"Export path is not a directory: {EXPORTS_DIR}"
        )

    for path in EXPORTS_DIR.iterdir():
        if (
            path.suffix.lower() != ".xlsx"
            or path.is_symlink()
            or not path.is_file()
        ):
            continue
        path.unlink()
        logger.info("Removed generated export %s", path)
        removed += 1

    logger.info("Export flush completed. Files removed=%d", removed)

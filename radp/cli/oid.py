import argparse
import logging

from radp.bootstrap.runtime import get_runtime
from radp.config.paths import OID_REGISTRY_FIXTURE_PATH

logger = logging.getLogger(__name__)


def sync_registry(_args: argparse.Namespace) -> None:
    """Merge seed OID definitions into the database without resetting it."""
    changed = get_runtime().bootstrap.initialize()
    logger.info(
        "OID registry sync completed. Definitions inserted or enriched=%d",
        changed,
    )


def export_registry(_args: argparse.Namespace) -> None:
    runtime = get_runtime()
    count = runtime.oid_exporter.export(OID_REGISTRY_FIXTURE_PATH)
    logger.info(
        "Exported %d OID definitions to %s", count, OID_REGISTRY_FIXTURE_PATH
    )

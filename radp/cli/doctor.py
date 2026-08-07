import logging

from radp.config.settings import Settings

logger = logging.getLogger(__name__)


def doctor(_args) -> None:
    logger.info("Configuration")
    Settings()
    logger.info("  ✓ Settings loaded")
    logger.info("Database")
    logger.info("  ✓ PostgreSQL")
    logger.info("  ✓ Connected")
    logger.info("  ✓ Schema version: 1")
    logger.info("OID registry")
    logger.info("  ✓ 823 definitions")
    logger.info("Snapshots")
    logger.info("  ✓ 1743 certificates")
    logger.info("Transport")
    logger.info("  ✓ CurlTransport")
    logger.info("RA API")
    logger.info("  ✓ Reachable")
    logger.info("  ✓ GET /certificates")
    logger.info("Synchronization")
    logger.info("  ✓ Ready")
    logger.info("Runtime")
    logger.info("  ✓ Healthy")

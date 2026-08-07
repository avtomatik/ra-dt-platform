import logging

from radp.application.reporting.certificates import CertificateReportService
from radp.application.synchronization.certificates import \
    CertificateSynchronizationService
from radp.bootstrap.oid_registry import OIDRegistryInitializer
from radp.config.settings import Settings
from radp.domain.snapshots.factory import CertificateSnapshotFactory
from radp.infrastructure.persistence.database import (create_engine_from_url,
                                                      create_session_factory)
from radp.infrastructure.persistence.repositories.oid_repository import \
    OIDRepository
from radp.infrastructure.persistence.repositories.snapshot_repository import \
    SnapshotRepository
from radp.infrastructure.ra_api.client import RAClient
from radp.infrastructure.transport.factory import create_transport

logger = logging.getLogger(__name__)


class Runtime:
    def __init__(self) -> None:
        self.settings = Settings()
        #######################################################################
        # Persistence
        #######################################################################
        self.engine = create_engine_from_url(self.settings.database_url)
        self.session_factory = create_session_factory(self.engine)
        self.oid_repository = OIDRepository(self.session_factory)
        self.snapshot_repository = SnapshotRepository(self.session_factory)
        #######################################################################
        # RA API
        #######################################################################
        self.transport = create_transport(self.settings)
        self.client = RAClient(self.transport)
        #######################################################################
        # Domain services
        #######################################################################
        self.snapshot_factory = CertificateSnapshotFactory(self.oid_repository)
        #######################################################################
        # Application services
        #######################################################################
        self.synchronization = CertificateSynchronizationService(
            client=self.client,
            snapshots=self.snapshot_repository,
            factory=self.snapshot_factory,
        )
        self.reporting = CertificateReportService(self.snapshot_repository)

        logger.info("Transport=%s", self.settings.transport)
        logger.info("Database=%s", self.settings.database_name)

    def initialize(self):
        OIDRegistryInitializer(self.oid_repository).initialize()
        self.synchronization.synchronize()

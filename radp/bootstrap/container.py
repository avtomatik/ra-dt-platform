"""Application composition root: dependencies are constructed lazily."""

from functools import cached_property

from radp.application.doctor.service import DoctorService
from radp.application.orchestration.bootstrap import BootstrapOrchestrator
from radp.application.orchestration.synchronization import \
    SynchronizationOrchestrator
from radp.application.reporting.certificates import CertificateReportService
from radp.application.reporting.oid_registry import OIDRegistryExporter
from radp.application.synchronization.certificates import \
    CertificateSynchronizer
from radp.config.paths import OID_REGISTRY_FIXTURE_PATH
from radp.config.settings import Settings
from radp.domain.certificate.factory import CertificateFactory
from radp.infrastructure.persistence.database import Database
from radp.infrastructure.persistence.repositories.certificate_query import \
    CertificateQueryRepository
from radp.infrastructure.persistence.repositories.certificate_repository import \
    CertificateRepository
from radp.infrastructure.persistence.repositories.oid_repository import \
    OIDRepository
from radp.infrastructure.ra_api.client import RAClient
from radp.infrastructure.transport.factory import create_transport


class Container:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()

    @cached_property
    def database(self) -> Database:
        return Database(self.settings.database.url)

    @cached_property
    def oid_repository(self) -> OIDRepository:
        return OIDRepository(self.database.engine)

    @cached_property
    def certificate_repository(self) -> CertificateRepository:
        return CertificateRepository(self.database.engine)

    @cached_property
    def certificate_queries(self) -> CertificateQueryRepository:
        return CertificateQueryRepository(self.database.engine)

    @cached_property
    def transport(self):
        return create_transport(self.settings)

    @cached_property
    def client(self) -> RAClient:
        return RAClient(self.transport)

    @cached_property
    def certificate_factory(self) -> CertificateFactory:
        return CertificateFactory(self.oid_repository)

    @cached_property
    def certificate_synchronizer(self) -> CertificateSynchronizer:
        return CertificateSynchronizer(
            self.client, self.certificate_repository, self.certificate_factory
        )

    @cached_property
    def synchronization(self) -> SynchronizationOrchestrator:
        return SynchronizationOrchestrator(self.certificate_synchronizer)

    @cached_property
    def bootstrap(self) -> BootstrapOrchestrator:
        return BootstrapOrchestrator(
            self.oid_repository, OID_REGISTRY_FIXTURE_PATH
        )

    @cached_property
    def oid_exporter(self) -> OIDRegistryExporter:
        return OIDRegistryExporter(self.oid_repository)

    @cached_property
    def reporting(self) -> CertificateReportService:
        return CertificateReportService(self.certificate_queries)

    @cached_property
    def doctor(self) -> DoctorService:
        return DoctorService(
            settings=self.settings,
            database=self.database,
            oids=self.oid_repository,
            certificates=self.certificate_queries,
            client=self.client,
            runtime_ready=True,
        )

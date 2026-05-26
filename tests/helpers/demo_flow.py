import logging

from rads_explorer.config.paths import EXPORTS_DIR

logger = logging.getLogger(__name__)


class DemoFlow:
    def __init__(
        self,
        certificate_service,
        cert_request_service,
        user_service,
        exporter,
        reports,
    ):
        self.certificates = certificate_service
        self.requests = cert_request_service
        self.users = user_service
        self.exporter = exporter
        self.reports = reports

    def run(self):
        logger.info("=" * 70)
        logger.info("GOST RA CLIENT DEMO")
        logger.info("=" * 70)

        # =====================================================================
        # A — Certificates
        # =====================================================================
        certificates = self.certificates.list_certificates()

        logger.info("[A] Certificates")
        logger.info("Count: %d", len(certificates.items))

        for cert in certificates.items[:5]:
            logger.info("=" * 54)
            logger.info(
                """
                CN: %s
                SNILS: %s
                Serial: %s
                Status: %s
                Valid: %s - %s""",
                cert.name_attributes.common_name,
                cert.name_attributes.snils,
                cert.serial_number,
                cert.status,
                cert.not_before,
                cert.not_after,
            )
            logger.info("=" * 54)

        # =====================================================================
        # B — Detail
        # =====================================================================
        first = certificates.items[0]

        detail = self.certificates.get_certificate(first.serial_number)

        logger.info("[B] Certificate detail")
        logger.info("Subject: %s", detail.subject)
        logger.info("Issuer: %s", detail.issuer)
        logger.info("X509: %s", detail.x509.subject)

        # =====================================================================
        # C — Reports
        # =====================================================================
        logger.info("[C] Reports")

        expiring = self.reports.expiring_certificates_report(365)

        if len(expiring.data) > 0:
            logger.info("Expiring: %d", len(expiring.data))

            issuer = self.reports.certificates_inventory_report()

            logger.info("Issuers: %s", issuer.data)

        # =====================================================================
        # D — Export
        # =====================================================================
        logger.info("[D] XLSX Export")

        path = EXPORTS_DIR / "ra-ds-explorer-demo.xlsx"

        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
        self.exporter.export(expiring, path)

        logger.info("Created: %s", path)
        logger.info("DEMO COMPLETE")

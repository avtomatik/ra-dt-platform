from enum import StrEnum

from radp.domain.models.certificate import CertificateStatus


class CertificateReportStatus(StrEnum):
    ALL = "ALL"
    VALID = "VALID"


class CertificateClassification(StrEnum):
    KEY_CARRIER = "Сертификат на ключевом носителе"
    CORPORATE = "Корпоративный сертификат"


CERTIFICATE_STATUS_LABELS: dict[CertificateStatus, str] = {
    CertificateStatus.VALID: "Действителен",
    CertificateStatus.REVOKED: "Отозван",
    CertificateStatus.EXPIRED: "Истёк",
    CertificateStatus.UNKNOWN: "Неизвестен",
}

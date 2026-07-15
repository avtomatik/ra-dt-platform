from typing import Any

from pydantic import ConfigDict

from .base import DomainModel


class NameAttributes(DomainModel):
    model_config = ConfigDict(extra="allow")

    # =========================================================================
    # Subject attributes
    # =========================================================================
    common_name: str | None
    surname: str | None
    given_name: str | None
    country_name: str | None
    locality_name: str | None
    state_or_province_name: str | None
    street_address: str | None
    organization_name: str | None
    organizational_unit_name: str | None
    title: str | None
    # =========================================================================
    # Russian subject attributes
    # =========================================================================
    inn: str | None
    snils: str | None
    guid: str | None
    legal_entity_inn: str | None
    ogrn: str | None
    # =========================================================================
    # PKCS #9
    # =========================================================================
    email_address: str | None
    unstructured_name: str | None
    # =========================================================================
    # Microsoft
    # =========================================================================
    user_principal_name: str | None
    certificate_template: str | None
    # =========================================================================
    # Russian certificate extensions
    # =========================================================================
    signature_device: str | None
    issuer_signature_and_ca_tools: str | None
    identity_verification_method: str | None
    # =========================================================================
    # GOST algorithms
    # =========================================================================
    gost3410_2012_256_public_key: str | None
    gost3411_2012_256_signature: str | None
    # =========================================================================
    # PKIX
    # =========================================================================
    authority_information_access: str | None
    ocsp: str | None
    ca_issuers: str | None
    # =========================================================================
    # X.509 v3 extensions
    # =========================================================================
    subject_key_identifier: str | None
    key_usage: str | None
    private_key_usage_period: str | None
    crl_distribution_points: str | None
    certificate_policies: str | None
    authority_key_identifier: str | None
    extended_key_usage: str | None
    # =========================================================================
    # Extended Key Usage (EKU)
    # =========================================================================
    smartcard_login: str | None

    def raw(self) -> dict[str, Any]:
        return self.model_extra or {}

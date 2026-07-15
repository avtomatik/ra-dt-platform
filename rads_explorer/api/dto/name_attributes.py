from typing import Any

from pydantic import ConfigDict, Field

from rads_explorer.certificate_domain.constants.oids import OID

from .base import DTOModel


class NameAttributes(DTOModel):
    model_config = ConfigDict(extra="allow")

    # =========================================================================
    # Subject attributes
    # =========================================================================
    common_name: str | None = Field(None, validation_alias=OID.CN)
    surname: str | None = Field(None, validation_alias=OID.SN)
    given_name: str | None = Field(None, validation_alias=OID.GIVEN_NAME)
    country_name: str | None = Field(None, validation_alias=OID.C)
    locality_name: str | None = Field(None, validation_alias=OID.L)
    state_or_province_name: str | None = Field(None, validation_alias=OID.S)
    street_address: str | None = Field(None, validation_alias=OID.STREET)
    organization_name: str | None = Field(None, validation_alias=OID.O)
    organizational_unit_name: str | None = Field(None, validation_alias=OID.OU)
    title: str | None = Field(None, validation_alias=OID.T)
    # =========================================================================
    # Russian subject attributes
    # =========================================================================
    inn: str | None = Field(None, validation_alias=OID.INN)
    snils: str | None = Field(None, validation_alias=OID.SNILS)
    guid: str | None = Field(None, validation_alias=OID.GUID)
    legal_entity_inn: str | None = Field(
        None, validation_alias=OID.LEGAL_ENTITY_INN
    )
    ogrn: str | None = Field(None, validation_alias=OID.OGRN)
    # =========================================================================
    # PKCS #9
    # =========================================================================
    email_address: str | None = Field(None, validation_alias=OID.EMAIL_ADDRESS)
    unstructured_name: str | None = Field(
        None, validation_alias=OID.UNSTRUCTURED_NAME
    )
    # =========================================================================
    # Microsoft
    # =========================================================================
    user_principal_name: str | None = Field(
        None, validation_alias=OID.USER_PRINCIPAL_NAME
    )
    certificate_template: str | None = Field(
        None, validation_alias=OID.CERTIFICATE_TEMPLATE
    )
    # =========================================================================
    # Russian certificate extensions
    # =========================================================================
    signature_device: str | None = Field(
        None, validation_alias=OID.SIGNATURE_DEVICE
    )
    issuer_signature_and_ca_tools: str | None = Field(
        None, validation_alias=OID.ISSUER_SIGNATURE_AND_CA_TOOLS
    )
    identity_verification_method: str | None = Field(
        None, validation_alias=OID.IDENTITY_VERIFICATION_METHOD
    )
    # =========================================================================
    # GOST algorithms
    # =========================================================================
    gost3410_2012_256_public_key: str | None = Field(
        None, validation_alias=OID.GOST3410_2012_256_PUBLIC_KEY
    )
    gost3411_2012_256_signature: str | None = Field(
        None, validation_alias=OID.GOST3411_2012_256_SIGNATURE
    )
    # =========================================================================
    # PKIX
    # =========================================================================
    authority_information_access: str | None = Field(
        None, validation_alias=OID.AUTHORITY_INFORMATION_ACCESS
    )
    ocsp: str | None = Field(None, validation_alias=OID.OCSP)
    ca_issuers: str | None = Field(None, validation_alias=OID.CA_ISSUERS)
    # =========================================================================
    # X.509 v3 extensions
    # =========================================================================
    subject_key_identifier: str | None = Field(
        None, validation_alias=OID.SUBJECT_KEY_IDENTIFIER
    )
    key_usage: str | None = Field(None, validation_alias=OID.KEY_USAGE)
    private_key_usage_period: str | None = Field(
        None, validation_alias=OID.PRIVATE_KEY_USAGE_PERIOD
    )
    crl_distribution_points: str | None = Field(
        None, validation_alias=OID.CRL_DISTRIBUTION_POINTS
    )
    certificate_policies: str | None = Field(
        None, validation_alias=OID.CERTIFICATE_POLICIES
    )
    authority_key_identifier: str | None = Field(
        None, validation_alias=OID.AUTHORITY_KEY_IDENTIFIER
    )
    extended_key_usage: str | None = Field(
        None, validation_alias=OID.EXTENDED_KEY_USAGE
    )
    # =========================================================================
    # Extended Key Usage (EKU)
    # =========================================================================
    smartcard_login: str | None = Field(
        None, validation_alias=OID.SMARTCARD_LOGIN
    )

    def raw(self) -> dict[str, Any]:
        return self.model_extra or {}

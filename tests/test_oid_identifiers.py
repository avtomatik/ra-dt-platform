from radp.domain.oid import OID


def test_oid_enum_contains_existing_reporting_identifiers():
    assert OID.CN.value == "2.5.4.3"
    assert OID.GUID.value == "1.2.643.3.168.7"
    assert OID.OGRN.value == "1.2.643.100.1"
    assert OID.CERTIFICATE_TEMPLATE.value == "1.3.6.1.4.1.311.21.7"


def test_oid_enum_is_string_compatible_for_dictionary_lookup():
    values = {OID.GUID.value: "gid"}
    assert values[OID.GUID] == "gid"

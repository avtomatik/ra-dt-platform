"""Decoding helpers for Microsoft certificate-template extensions."""

import ast

_UTF8_STRING = 0x0C
_BMP_STRING = 0x1E
_SEQUENCE = 0x30
_MAX_LENGTH_OCTETS = 4


def _read_der_tlv(data: bytes, offset: int = 0) -> tuple[int, bytes, int]:
    """Read one definite-length DER tag/value at ``offset``.
    This deliberately supports only the small subset needed by the Microsoft
    template-name extension. It is not intended to be a general ASN.1 parser.
    """
    if offset < 0 or offset + 2 > len(data):
        raise ValueError("Truncated DER value.")
    tag = data[offset]
    first_length = data[offset + 1]
    cursor = offset + 2
    if first_length < 0x80:
        length = first_length
    else:
        length_octets = first_length & 0x7F
        if (
            length_octets == 0
            or length_octets > _MAX_LENGTH_OCTETS
            or cursor + length_octets > len(data)
        ):
            raise ValueError("Invalid DER length encoding.")
        encoded_length = data[cursor : cursor + length_octets]
        if encoded_length[0] == 0:
            raise ValueError("Non-canonical DER length encoding.")
        length = int.from_bytes(encoded_length, "big")
        if length < 0x80:
            raise ValueError("Non-canonical DER long-form length.")
        cursor += length_octets
    end = cursor + length
    if end > len(data):
        raise ValueError("Truncated DER content.")
    return tag, data[cursor:end], end


def _decode_template_string(tag: int, payload: bytes) -> str:
    if tag == _UTF8_STRING:
        decoded = payload.decode("utf-8", errors="strict")
    elif tag == _BMP_STRING:
        if len(payload) % 2:
            raise ValueError("BMPString content must have an even length.")
        decoded = payload.decode("utf-16-be", errors="strict")
    else:
        raise ValueError("Unsupported Microsoft template-name ASN.1 string.")
    normalized = decoded.strip()
    if not normalized:
        raise ValueError("Microsoft template name is empty.")
    return normalized


def decode_microsoft_template_name(payload: bytes | None) -> str | None:
    """Decode a Microsoft V1 certificate-template name extension.
    Microsoft specifies ``SEQUENCE { Name UTF8String }`` for OID
    1.3.6.1.4.1.311.20.2. Some deployed certificates use a bare BMPString;
    both encodings are accepted. Malformed optional metadata returns ``None``
    rather than preventing ingestion of an otherwise valid certificate.
    """
    if not isinstance(payload, bytes) or not payload:
        return None
    try:
        tag, content, end = _read_der_tlv(payload)
        if end != len(payload):
            return None
        if tag == _SEQUENCE:
            inner_tag, inner_content, inner_end = _read_der_tlv(content)
            if inner_end != len(content):
                return None
            return _decode_template_string(inner_tag, inner_content)
        return _decode_template_string(tag, content)
    except (UnicodeDecodeError, ValueError):
        return None


def decode_legacy_template_name(value: str | None) -> str | None:
    """Decode a V1 extension from the historical ``str(UnrecognizedExtension)``.
    Before RADP stored a dedicated ``template_name`` field, cryptography's
    repr-like value was persisted in the certificate JSONB payload. Parsing
    the bytes literal with ``ast.literal_eval`` is safe and lets old records
    benefit from the V1 decoder without fetching the certificate again.
    """
    if not isinstance(value, str):
        return None
    marker = "value="
    start = value.find(marker)
    end = value.rfind(")>")
    if start < 0 or end <= start:
        return None
    candidate = value[start + len(marker) : end].strip()
    try:
        raw_value = ast.literal_eval(candidate)
    except (SyntaxError, ValueError):
        return None
    if not isinstance(raw_value, bytes):
        return None
    return decode_microsoft_template_name(raw_value)

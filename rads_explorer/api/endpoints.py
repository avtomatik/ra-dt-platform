API_PREFIX = "/api/ra"

CERTIFICATES = f"{API_PREFIX}/certificates"
USERS = f"{API_PREFIX}/users"
CERT_REQUESTS = f"{API_PREFIX}/certRequests"
TEMPLATES = f"{API_PREFIX}/templates"


def certificate_by_serial(serial_number: str) -> str:
    return f"{CERTIFICATES}/serialNumber/{serial_number}"

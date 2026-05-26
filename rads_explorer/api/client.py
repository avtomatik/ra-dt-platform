from rads_explorer.api.endpoints import (CERT_REQUESTS, CERTIFICATES, USERS,
                                         certificate_by_serial)
from rads_explorer.api.pagination import paginate
from rads_explorer.api.parsers import (parse_cert_request, parse_cert_requests,
                                       parse_certificate_detail,
                                       parse_certificates, parse_user,
                                       parse_users)
from rads_explorer.infrastructure.transport.validators import (ensure_json,
                                                               ensure_success)


class CertificatesApi:
    def __init__(self, transport):
        self.transport = transport

    def list(self):
        response = self.transport.get(CERTIFICATES)
        data = ensure_json(ensure_success(response))
        return parse_certificates(data)

    def _fetch_href(self, href: str):
        response = self.transport.get(href)
        data = ensure_json(ensure_success(response))
        return parse_certificates(data)

    def iter_all(self):
        first_page = self.list()
        yield from paginate(first_page, self._fetch_href)

    def list_all(self):
        return list(self.iter_all())

    def get_by_id(self, certificate_id: str):
        response = self.transport.get(f"{CERTIFICATES}/{certificate_id}")
        data = ensure_json(ensure_success(response))
        return parse_certificate_detail(data)

    def get_by_serial(self, serial_number: str):
        response = self.transport.get(certificate_by_serial(serial_number))
        data = ensure_json(ensure_success(response))
        return parse_certificate_detail(data)

    def search(self, query):
        response = self.transport.get(CERTIFICATES, params={"value": query})
        # =====================================================================
        # Search Options
        # =====================================================================
        # =====================================================================
        # {"filter": "test"}
        # {"q": "test"}
        # {"query": "test"}
        # {"search": "test"}
        # {"text": "test"}
        # =====================================================================
        data = ensure_json(ensure_success(response))
        return parse_certificates(data)


class CertificateRequestsApi:
    def __init__(self, transport):
        self.transport = transport

    def list(self):
        response = self.transport.get(CERT_REQUESTS)
        data = ensure_json(ensure_success(response))
        return parse_cert_requests(data)

    def get(self, cert_request_id):
        response = self.transport.get(f"{CERT_REQUESTS}/{cert_request_id}")
        data = ensure_json(ensure_success(response))
        return parse_cert_request(data)


class UsersApi:
    def __init__(self, transport):
        self.transport = transport

    def list(self):
        response = self.transport.get(USERS)
        data = ensure_json(ensure_success(response))
        return parse_users(data)

    def get(self, user_id):
        response = self.transport.get(f"{USERS}/{user_id}")
        data = ensure_json(ensure_success(response))
        return parse_user(data)


class RADSClient:
    def __init__(self, transport):
        self.transport = transport
        self.certificates = CertificatesApi(transport)
        self.cert_requests = CertificateRequestsApi(transport)
        self.users = UsersApi(transport)

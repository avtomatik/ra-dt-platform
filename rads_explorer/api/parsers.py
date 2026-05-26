from rads_explorer.api.schemas.cert_request import CertificateRequest
from rads_explorer.api.schemas.certificate import CertificateDetail
from rads_explorer.api.schemas.responses import (CertificateRequestsResponse,
                                                 CertificatesResponse,
                                                 UsersResponse)
from rads_explorer.api.schemas.user import User
from rads_explorer.application.exceptions import (APIContractError,
                                                  ValidationError)


def _parse(model, data):
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        raise APIContractError(
            f"API schema mismatch for {model.__name__}"
        ) from exc


def parse_certificates(data):
    return _parse(CertificatesResponse, data)


def parse_certificate_detail(data):
    return _parse(CertificateDetail, data)


def parse_cert_request(data):
    return _parse(CertificateRequest, data)


def parse_cert_requests(data):
    return _parse(CertificateRequestsResponse, data)


def parse_cert_request_detail(data):
    return parse_cert_request(data)


def parse_user(data):
    return _parse(User, data)


def parse_users(data):
    return _parse(UsersResponse, data)

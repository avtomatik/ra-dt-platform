from rads_explorer.infrastructure.transport.exceptions import (HTTPError,
                                                               JSONDecodeError)


def ensure_success(response):
    if not response.ok:
        raise HTTPError(response.status_code, response.body)
    return response


def ensure_json(response):
    if response.json_data is None:
        raise JSONDecodeError(response.body)
    return response.json_data

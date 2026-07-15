def test_cert_requests_list(client):
    result = client.cert_requests.list()
    assert len(result.items) > 0


def test_certificates_list(client):
    result = client.certificates.list_page()
    assert len(result.items) > 0


def test_certificates_iter_all(client):
    certs = list(client.certificates.iter_all())
    assert len(certs) > 0


def test_users_list(client):
    result = client.users.list()
    assert len(result.items) > 0

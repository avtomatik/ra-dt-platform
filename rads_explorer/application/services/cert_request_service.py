class CertificateRequestService:
    def __init__(self, api_client):
        self.api = api_client

    def list_requests(self):
        return self.api.cert_requests.list()

    def get_request(self, request_id: str):
        return self.api.cert_requests.get(request_id)

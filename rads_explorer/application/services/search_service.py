class SearchService:
    def __init__(self, api_client):
        self.api = api_client

    def certificates(self, query: str):
        return self.api.certificates.search(query)

    def users(self, query: str):
        raise NotImplementedError("User search is not implemented yet.")

class UserService:
    def __init__(self, api_client):
        self.api = api_client

    def list_users(self):
        return self.api.users.list()

    def get_user(self, user_id: str):
        return self.api.users.get(user_id)

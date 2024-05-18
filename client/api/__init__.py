import os

from aiohttp import ClientSession
from cryptography.fernet import Fernet


class ServerApi:
    _cipher = Fernet(os.getenv("CIPHER"))
    _address = os.getenv("BACKEND")

    def __init__(self):
        self._headers = {
            "Authorization": '',
            "x-service-name": "Psychological",
            "api-key": os.getenv("API_KEY")
        }

    async def add_user(self, user_id: str):
        async with ClientSession(self._address) as session:
            async with session.post(
                    '/users', json={'user_id': user_id},
                    headers=self._headers
            ) as response:
                return response

    async def get_user(self, user_id: str):
        async with ClientSession(self._address) as session:
            async with session.get(
                    f'/users/{self._cipher.encrypt(user_id.encode())}',
                    headers=self._headers
            ) as response:
                return response

    async def authentication(self, password: str, user_id: str):
        async with ClientSession(self._address) as session:
            async with session.post('/users/login', json={
                    'user_id': user_id,
                    "password": password,
            }, headers=self._headers) as response:
                return response

    async def get_targets(self, token: str):
        async with ClientSession(self._address) as session:
            self._headers["Authorization"] = f"Bearer {token}"
            async with session.get(
                    f'/targets',
                    headers=self._headers
            ) as response:
                return response

    async def invert_notifications(self, user_id: str):
        async with ClientSession(self._address) as session:
            async with session.patch(
                    "/users/notifications",
                    json={"user_id": user_id},
                    headers=self._headers
            ) as response:
                return response

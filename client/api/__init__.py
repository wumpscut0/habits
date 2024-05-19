import os
from functools import wraps

from aiohttp import ClientSession
from aiohttp.web_response import Response
from cryptography.fernet import Fernet

from client.utils.loggers import errors


class ServerApi:
    _cipher = Fernet(os.getenv("CIPHER"))
    _address = os.getenv("BACKEND")

    _logs = {
        401: "Unauthorized"
    }

    def __init__(self):
        self._headers = {
            "Authorization": '',
            "x-service-name": "Psychological",
            "api-key": os.getenv("API_KEY")
        }

    @staticmethod
    def _async_request_middleware(request):
        @wraps(request)
        async def wrapper(self, *args, **kwargs) -> Response:
            data, code = await request(self, *args, **kwargs)
            if code == 401:
                errors.error(f"401 Unauthorized. Worker: {request.__name__}")
            elif code == 500:
                errors.error(f"500 Internal server error.")
            return data
        return wrapper

    @_async_request_middleware
    async def add_user(self, user_id: str):
        async with ClientSession(self._address) as session:
            async with session.post(
                    '/users', json={'user_id': user_id},
                    headers=self._headers
            ) as response:
                return await response.json(), response.status

    @_async_request_middleware
    async def get_user(self, user_id: str):
        async with ClientSession(self._address) as session:
            async with session.get(
                    f'/users/{self._cipher.encrypt(user_id.encode()).decode()}',
                    headers=self._headers
            ) as response:
                return await response.json(), response.status

    @_async_request_middleware
    async def authentication(self, password: str, user_id: str):
        async with ClientSession(self._address) as session:
            async with session.post('/users/login', json={
                    'user_id': user_id,
                    "password": password,
            }, headers=self._headers) as response:
                return await response.json(), response.status

    @_async_request_middleware
    async def get_targets(self, token: str):
        async with ClientSession(self._address) as session:
            self._headers["Authorization"] = f"Bearer {token}"
            async with session.get(
                    f'/targets',
                    headers=self._headers
            ) as response:
                return await response.json(), response.status

    @_async_request_middleware
    async def invert_notifications(self, user_id: str):
        async with ClientSession(self._address) as session:
            async with session.patch(
                    "/users/notifications",
                    json={"user_id": user_id},
                    headers=self._headers
            ) as response:
                return await response.json(), response.status

    @_async_request_middleware
    async def increase_progress(self):
        async with ClientSession(self._address) as session:
            async with session.patch(
                    f'/targets/progress',
                    headers=self._headers
            ) as response:
                return await response.json(), response.status

    @_async_request_middleware
    async def get_users(self):
        async with ClientSession(self._address) as session:
            async with session.get(
                    f'/users',
                    headers=self._headers
            ) as response:
                return await response.json(), response.status

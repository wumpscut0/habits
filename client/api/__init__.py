import os
from functools import wraps

from aiohttp import ClientSession
from aiohttp.web_response import Response
from cryptography.fernet import Fernet

from client.utils.loggers import errors


class Api:
    _cipher = Fernet(os.getenv("CIPHER"))
    _address = os.getenv("BACKEND")

    def __init__(self):
        self._headers = {
            "Authorization": '',
            "x-service-name": "Psychological",
            "api-key": os.getenv("API_KEY")
        }

    @staticmethod
    def _async_request_middleware(request):
        @wraps(request)
        async def wrapper(self, *args, **kwargs):
            data, code = await request(self, *args, **kwargs)
            if code == 401:
                errors.error(f"401 Unauthorized. Worker: {request.__name__}")
            elif code == 500:
                errors.error(f"500 Internal server error.")
            return data, code
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
    async def authentication(self, user_id: str, password: str | None = None):
        async with ClientSession(self._address) as session:
            async with session.post('/users/login', json={
                    'user_id': user_id,
                    "password": password,
            }, headers=self._headers) as response:
                return await response.json(), response.status

    @_async_request_middleware
    async def get_targets(self, token: str):
        self._headers["Authorization"] = f"Bearer {token}"
        async with ClientSession(self._address) as session:
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

    @_async_request_middleware
    async def update_password(self, user_id: str, hash_: str):
        async with ClientSession(self._address) as session:
            async with session.put(
                f"/users/password",
                json={
                    "user_id": user_id,
                    "hash": hash_,
                },
                headers=self._headers
            ) as response:
                return await response.json(), response.status

    async def delete_password(self, token: str):
        self._headers["Authorization"] = f"Bearer {token}"
        async with ClientSession(self._address) as session:
            async with session.delete(
                    f"/users/password",
                    headers=self._headers
            ) as response:
                return await response.json(), response.status

    async def update_email(self, token: str, email: str):
        self._headers["Authorization"] = f"Bearer {token}"
        async with ClientSession(self._address) as session:
            async with session.put(
                f"/users/email",
                json={"email": email},
                headers=self._headers
            ) as response:
                return await response.json(), response.status

    async def delete_email(self, token: str):
        self._headers["Authorization"] = f"Bearer {token}"
        async with ClientSession(self._address) as session:
            async with session.delete(
                    f"/users/email",
                    headers=self._headers
            ) as response:
                return await response.json(), response.status

    async def update_notifications_time(self, token: str, hour: int, minute: int):
        self._headers["Authorization"] = f"Bearer {token}"
        async with ClientSession(self._address) as session:
            async with session.put(
                    "/users/notifications",
                    json={"hour": hour, "minute": minute},
                    headers=self._headers
            ) as response:
                return await response.json(), response.status

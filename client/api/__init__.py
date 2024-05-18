import os
from functools import wraps
from typing import Awaitable

from aiohttp import ClientSession
from aiohttp.web_response import Response
from cryptography.fernet import Fernet

from client.bot import BotControl


class UnexpectedError(Exception):
    def __init__(self, message="Internal server error", code=None):
        super().__init__(message)
        self.code = code


class Unauthorized(Exception):
    def __init__(self, message="Unauthorized"):
        super().__init__(message)
        self.code = 401


class ExpiredToken(Exception):
    def __init__(self, message="Expired token"):
        super().__init__(message)
        self.code = 419


class InternalServerError(Exception):
    def __init__(self, message="Internal server error"):
        super().__init__(message)
        self.code = 500


class ServerApi:
    _cipher = Fernet(os.getenv("CIPHER"))

    def __init__(self, bot_control: BotControl):
        self.bot_control = bot_control
        self.user_id = bot_control.user_id
        self._headers = {
            "Authorization": '',
            "x-service-name": "Psychological",
            "api-key": os.getenv("API_KEY")
        }
        self.statuses = {
            # 401: self.bot_control.open_session(),
            500: self.bot_control.close_session(),
        }

    @staticmethod
    def _async_request_middleware(request):
        @wraps(request)
        async def wrapper(self: ServerApi, *args, **kwargs) -> Response:
            async with ClientSession(os.getenv("BACKEND")) as session:
                response = await request(self, session, *args, **kwargs)
                # await self.statuses.get(response.status, self.bot_control.handling_unexpected_error(response))
                return response
        return wrapper

    @_async_request_middleware
    async def add_user(self, session: ClientSession):
        async with session.post(
                '/users', json={'user_id': self.user_id},
                headers=self._headers
        ) as response:
            return response

    @_async_request_middleware
    async def get_user(self, session: ClientSession):
        async with session.get(
                f'/users/{self._cipher.encrypt(bytes(self.user_id))}',
                headers=self._headers
        ) as response:
            return response

    @_async_request_middleware
    async def authentication(self, session: ClientSession, password: str):
        async with session.post('/users/login', json={
            'user_id': self.bot_control.user_id,
            "password": password,
        }, headers=self._headers) as response:
            return response

    @_async_request_middleware
    async def get_targets(self, session: ClientSession):
        self._headers["Authorization"] = f"Bearer {self.bot_control.storage.user_token}"
        async with session.get(
                f'/targets',
                headers=self._headers
        ) as response:
            return response



import os
from functools import wraps
from typing import Awaitable, Coroutine, Callable, Dict

from aiohttp import ClientSession
from cryptography.fernet import Fernet

from client.bot import BotControl
from client.controller import Interface
from client.markups.basic import AuthenticationWithPassword
from client.utils.redis import Storage


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
        self.user_id = bot_control.chat_id
        self._headers = {
            "Authorization": None
        }
        self.statuses = {
            419: self.bot_control.server.authentication(),
            401: self.bot_control.close_session(),
            500: Awaitable,
        }

    @staticmethod
    def async_request_middleware(request):
        @wraps(request)
        async def wrapper(self: ServerApi, *args, **kwargs) -> Dict | str | None:
            async with ClientSession(os.getenv("BACKEND")) as session:
                response = await request(self, session, *args, **kwargs)
                await self.statuses.get(response.status, self.bot_control.handling_unexpected_error(response))
                if response.headers["Content-Type"] == "application/json":
                    return await response.json()
                elif response.headers["Content-Type"] == "mimi/text":
                    return await response.text()
        return wrapper

    @async_request_middleware
    async def add_user(self, session: ClientSession):
        self._headers["Authorization"] = self.bot_control.storage.service_token
        async with session.post(
                '/users', json={'user_id': self.user_id},
                headers=self._headers
        ) as response:
            return response

    @async_request_middleware
    async def get_user(self, session: ClientSession):
        self._headers["Authorization"] = self.bot_control.storage.service_token
        async with session.get(
                f'/users/{self._cipher.encrypt(bytes(self.user_id))}',
                headers=self._headers
        ) as response:
            return response

    @async_request_middleware
    async def get_targets(self, session: ClientSession):
        self._headers["Authorization"] = self.bot_control.storage.user_id
        async with session.get(
                f'/targets',
                headers=self._headers
        ) as response:
            return response

    @async_request_middleware
    async def authentication(self):
        user = await self.get_user()
        if user is not None:
            hash_ = user.get("hash")
            if hash_ is not None:
                await AuthenticationWithPassword().open()
            else:
                response = await self._authorization()
                if response is not None:
                    self._interface.token = await response.text()
                    await self._interface.basic_manager.profile.open()

    async def _authorization(self):
        async with self._interface.session.post('/users/login', json={
            'user_id': self._interface.chat_id,
        }, headers={"Authorization": storage.get("service_key")}) as response:
            return await self._interface.response_middleware(response, self._authorization())

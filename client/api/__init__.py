import os

from aiohttp import ClientSession
from cryptography.fernet import Fernet


class Api:
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
                return await response.json(), response.status

    async def get_user(self, user_id: str):
        async with ClientSession(self._address) as session:
            async with session.get(
                    f'/users/{self._cipher.encrypt(str(user_id).encode()).decode()}',
                    headers=self._headers
            ) as response:
                return await response.json(), response.status

    async def authentication(self, user_id: str, password: str | None = None):
        async with ClientSession(self._address) as session:
            async with session.post('/users/login', json={
                    'user_id': user_id,
                    "password": password,
            }, headers=self._headers) as response:
                return await response.json(), response.status

    async def get_targets(self, token: str):
        self._headers["Authorization"] = f"Bearer {token}"
        async with ClientSession(self._address) as session:
            async with session.get(
                    f'/targets',
                    headers=self._headers
            ) as response:
                return await response.json(), response.status

    async def invert_notifications(self, user_id: str):
        async with ClientSession(self._address) as session:
            async with session.patch(
                    "/users/notifications",
                    json={"user_id": user_id},
                    headers=self._headers
            ) as response:
                return await response.json(), response.status

    async def increase_progress(self):
        async with ClientSession(self._address) as session:
            async with session.patch(
                    f'/targets/progress',
                    headers=self._headers
            ) as response:
                return await response.json(), response.status

    async def get_users(self):
        async with ClientSession(self._address) as session:
            async with session.get(
                    f'/users',
                    headers=self._headers
            ) as response:
                return await response.json(), response.status

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

    async with self._interface.session.post('/targets', json={
    #             "name": name,
    #             "border_progress": border
    #         }, headers={"Authorization": self._interface.token}) as response:

    async with self._interface.session.delete(
    #             f'/targets/{storage.get(f"target_id:{self._interface._user_id}")}',
    #             headers={"Authorization": self._interface.token}
    #         ) as response:

    #         async with (self._interface.session.get(f"/targets/{kwargs['target_id']}", headers={"Authorization": self._interface.token}) as response):

    #         async with self._interface.session.patch(f'/targets/{target_id}/invert', headers={"Authorization": self._interface.token}) as response:

    async with self._interface.session.patch(
    #                 f'/target/{target_id}', json={"name": name},
    #                 headers={"Authorization": self._interface.token}
    #             ) as response:
    #                 response = await self._interface.response_middleware(response)
    #                 if response is not None:
    #                     await self._interface.targets_manager.target.open(target_id=target_id)

    async with self._interface.session.patch(
    #                     f'/target/{target_id}', json={"name": description},
    #                     headers={"Authorization": self._interface.token}
    #             ) as response:
    #                 response = await self._interface.response_middleware(response)
    #                 if response is not None:
    #                     await self._interface.targets_manager.target.open(target_id=target_id)

    async with self._interface.session.get(
    #                 f"/target/{kwargs['target_id']}",
    #                 headers={"Authorization": self._interface._user_id}
    #         ) as response:
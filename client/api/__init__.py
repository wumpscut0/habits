import os

from aiohttp import ClientSession
from cryptography.fernet import Fernet


class Api:
    _cipher = Fernet(os.getenv("CIPHER"))
    _address = os.getenv("BACKEND")

    @classmethod
    def _headers(cls):
        return {
            "Authorization": '',
            "x-service-name": "Psychological",
            "api-key": os.getenv("API_KEY")
        }
    
    @classmethod
    async def add_user(cls, user_id: str):
        async with ClientSession(cls._address) as session:
            async with session.post(
                    '/users', json={'user_id': user_id},
                    headers=cls._headers()
            ) as response:
                return await response.json(), response.status

    @classmethod
    async def get_user(cls, user_id: str):
        async with ClientSession(cls._address) as session:
            async with session.get(
                    f'/users/{cls._cipher.encrypt(str(user_id).encode()).decode()}',
                    headers=cls._headers()
            ) as response:
                return await response.json(), response.status

    @classmethod
    async def authentication(cls, user_id: str, password: str | None = None):
        async with ClientSession(cls._address) as session:
            async with session.post('/users/login', json={
                    'user_id': user_id,
                    "password": password,
            }, headers=cls._headers()) as response:
                return await response.json(), response.status

    @classmethod
    async def get_targets(cls, token: str):
        headers = cls._headers()
        headers["Authorization"] = f"Bearer {token}"
        async with ClientSession(cls._address) as session:
            async with session.get(
                    f'/targets',
                    headers=headers
            ) as response:
                return await response.json(), response.status

    @classmethod
    async def invert_notifications(cls, user_id: str):
        async with ClientSession(cls._address) as session:
            async with session.patch(
                    "/users/notifications",
                    json={"user_id": user_id},
                    headers=cls._headers()
            ) as response:
                return await response.json(), response.status

    @classmethod
    async def increase_progress(cls):
        async with ClientSession(cls._address) as session:
            async with session.patch(
                    f'/targets/progress',
                    headers=cls._headers()
            ) as response:
                return await response.json(), response.status

    @classmethod
    async def get_users(cls):
        async with ClientSession(cls._address) as session:
            async with session.get(
                    f'/users',
                    headers=cls._headers()
            ) as response:
                return await response.json(), response.status

    @classmethod
    async def update_password(cls, user_id: str, hash_: str):
        async with ClientSession(cls._address) as session:
            async with session.put(
                f"/users/password",
                json={
                    "user_id": user_id,
                    "hash": hash_,
                },
                headers=cls._headers()
            ) as response:
                return await response.json(), response.status

    @classmethod
    async def delete_password(cls, token: str):
        headers = cls._headers()
        headers["Authorization"] = f"Bearer {token}"
        async with ClientSession(cls._address) as session:
            async with session.delete(
                    f"/users/password",
                    headers=headers
            ) as response:
                return await response.json(), response.status

    @classmethod
    async def update_email(cls, token: str, email: str):
        headers = cls._headers()
        headers["Authorization"] = f"Bearer {token}"
        async with ClientSession(cls._address) as session:
            async with session.put(
                f"/users/email",
                json={"email": email},
                headers=headers
            ) as response:
                return await response.json(), response.status

    @classmethod
    async def delete_email(cls, token: str):
        headers = cls._headers()
        headers["Authorization"] = f"Bearer {token}"
        async with ClientSession(cls._address) as session:
            async with session.delete(
                    f"/users/email",
                    headers=headers
            ) as response:
                return await response.json(), response.status

    @classmethod
    async def update_notifications_time(cls, token: str, hour: int, minute: int):
        headers = cls._headers()
        headers["Authorization"] = f"Bearer {token}"
        async with ClientSession(cls._address) as session:
            async with session.put(
                    "/users/notifications",
                    json={"hour": hour, "minute": minute},
                    headers=headers
            ) as response:
                return await response.json(), response.status

    @classmethod
    async def create_target(cls, token: str, name: str, border_progress: int, description: str | None = None):
        headers = cls._headers()
        headers["Authorization"] = f"Bearer {token}"
        async with ClientSession(cls._address) as session:
            async with session.post('/targets', json={
                "name": name,
                "border_progress": border_progress,
                "description": description
            }, headers=headers) as response:
                return await response.json(), response.status

    @classmethod
    async def delete_target(cls, token: str, target_id: int):
        headers = cls._headers()
        headers["Authorization"] = f"Bearer {token}"
        async with ClientSession(cls._address) as session:
            async with session.delete(
                f'/targets/{target_id}',
                headers=headers
            ) as response:
                return await response.json(), response.status

    @classmethod
    async def get_target(cls, token: str, target_id: int):
        headers = cls._headers()
        headers["Authorization"] = f"Bearer {token}"
        async with ClientSession(cls._address) as session:
            async with session.get(
                    f"/targets/{target_id}",
                    headers=headers
            ) as response:
                return await response.json(), response.status

    @classmethod
    async def invert_completed(cls, token: str, target_id: int):
        headers = cls._headers()
        headers["Authorization"] = f"Bearer {token}"
        async with ClientSession(cls._address) as session:
            async with session.patch(
                    f'/targets/{target_id}/invert',
                    headers=headers
            ) as response:
                return await response.json(), response.status

    @classmethod
    async def update_target(cls, token: str, target_id: int, *, name: str | None = None, description: str | None = None):
        headers = cls._headers()
        headers["Authorization"] = f"Bearer {token}"
        async with ClientSession(cls._address) as session:
            async with session.put(
                    f'/targets/{target_id}',
                    json={
                        "name": name,
                        "description": description
                    },
                    headers=headers
            ) as response:
                return await response.json(), response.status

import json
import os
import jwt
from aiohttp import ClientSession
from frontend.markups import Markup, ButtonWidget, CommonButtons, CommonTexts
from frontend.markups.login import Login
from frontend.markups.nickname import Nickname
from frontend.markups.password import Password


class SignUp(Markup):
    def __init__(self):
        super().__init__()
        self._nickname = Nickname()
        self._login = Login()
        self._password = Password()
        self._header = 'Fill all fields'
        self._text_map = {
            "nickname": CommonTexts.nickname(),
            "login": CommonTexts.login(),
            "password": CommonTexts.password(),
            "feedback": CommonTexts.feedback(),
        }
        self._markup_map = [
            {
                "nickname": ButtonWidget("🪪 Change nickname", "open_nickname"),
                "login": ButtonWidget("🆔 Change login", "open_login"),
                "password": ButtonWidget("🔑 Change password", "open_password")
            },
            {
                "sign_up": ButtonWidget('✅ Sign up', "try_sign_up")
            },
            {
                "back": CommonButtons.back("open_authorization")
            },
        ]

    @property
    def nickname(self):
        return self._nickname

    @property
    def login(self):
        return self._login

    @property
    def password(self):
        return self._password

    @property
    async def text(self):
        nickname = "❔" if self._nickname.nickname is None else self._nickname.nickname
        login = "❔" if self._login.login is None else self._login.login
        password = "❔" if self._password.hash is None else self._password.password
        await self._text_map['nickname'].update_text(data=nickname)
        await self._text_map['login'].update_text(data=login)
        await self._text_map['password'].update_text(data=password)
        return await super().text

    async def _reset(self):
        self._nickname = Nickname()
        self._login = Login()
        self._password = Password()
        for widget in self._text_map.values():
            widget.reset()

    async def try_sign_up(self, user_id: int, session: ClientSession):
        if not all((self._nickname.nickname, self._login.login, self._password.hash)):
            await self._text_map['feedback'].update_text(data='All fields required')
            return

        request = jwt.encode(
            {
                "telegram_id": user_id,
                "nickname": self._nickname.nickname,
                "login": self._login.login,
                "password": self._password.hash,
            },
            os.getenv('JWT')
        )
        async with session.post(f'/sign_up/{request}') as response:
            if response.status != 201:
                print((await response.json())['detail'])
                await self._text_map['feedback'].update_text(data="Unknown error")
                return

            await self._reset()
            await self._text_map['feedback'].update_text(data='Account created')

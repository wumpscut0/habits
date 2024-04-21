import os
import jwt
from aiohttp import ClientSession
from frontend import errors
from frontend.markups import Markup, ButtonWidget, CommonButtons, CommonTexts
from frontend.markups.login import Login
from frontend.markups.nickname import Nickname
from frontend.markups.password import AddPassword


class SignUp2(Markup):
    def __init__(self):
        super().__init__()
        self._init_related_nodes()
        self._init_data()

        self._init_header()
        self._init_text_map()
        self._init_markup_map()

    def _init_related_nodes(self):
        self._nickname = Nickname()
        self._login = Login()
        self._password = AddPassword()

    def _init_data(self):
        ...

    def _init_header(self):
        self._header = '🔏 Sign up'

    def _init_text_map(self):
        self._text_map = {
            "nickname": CommonTexts.nickname(),
            "login": CommonTexts.login(),
            "password": CommonTexts.password(),
            "feedback": CommonTexts.feedback(),
        }

    def _init_markup_map(self):
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
        await self._text_map['nickname'].update_text(data=self._nickname.text_map['nickname'].data)
        await self._text_map['login'].update_text(data=self._login.text_map['login'].data)
        await self._text_map['password'].update_text(data=self._password.text_map['password'].data)
        return await super().text

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
        async with session.post(f'/sign_up', json={'jwt': request}) as response:
            data = await response.json()
            if response.status != 201:
                errors.error(data['detail'])
                await self._text_map['feedback'].update_text(data=data['detail'])
                return

            self._init_related_nodes()
            self._init_text_map()
            await self._text_map['feedback'].update_text(data='Account created')
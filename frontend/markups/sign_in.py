import os
import re
import aiohttp
import jwt
from aiogram.utils.formatting import Bold, Italic
from aiohttp import ClientSession
from zxcvbn import zxcvbn
from passlib.hash import pbkdf2_sha256
from frontend.markups import Markup, TextWidget, ButtonWidget, CommonButtons, CommonTexts
from config import *


class Nickname(Markup):
    def __init__(self):
        super().__init__()
        self._nickname = None

        self._header = "Choose the nickname"
        self._text_map = {
            'nickname': CommonTexts.nickname(),
            'feedback': CommonTexts.feedback(),
        }
        self._markup_map = [
            {
                'accept': CommonButtons.accept('sign_up')
            },
        ]

    @property
    def nickname(self):
        return self._nickname

    async def update_nickname(self, nickname):
        if not re.fullmatch(r'\w{3,10}', nickname, flags=re.I):
            await self._text_map['feedback'].update_text(
                data=Italic(f"Nickname {nickname} not allowed."
                            " Nickname must contains only latin symbols or signs '_' or digits."),
                mark=DENIAL
            )
        else:
            self._nickname = nickname
            await self._text_map['nickname'].update_text(data=Italic(nickname))
            await self._text_map['feedback'].update_text(data=Italic("Nickname allowed"), mark=OK)


class Login(Markup):
    def __init__(self):
        super().__init__()
        self._login = None

        self._header = 'Choose the login'
        self._text_map = {
            "login": CommonTexts.login(),
            "feedback": CommonTexts.feedback()
        }
        self._markup_map = [
            {
                "accept": CommonButtons.accept('sign_up')
            },
        ]

    @property
    def login(self):
        return self._login

    async def update_login(self, login, session: ClientSession):
        if not re.fullmatch(r'\w{3,10}', login, flags=re.I):
            await self._text_map['feedback'].update_text(
                data=Bold("Login must contains only latin symbols or signs '_' or digits."),
                mark=DENIAL
            )
        else:
            async with session.get(f'/verify_login/{login}') as response:
                if response.status == 409:
                    await self._text_map['feedback'].update_text(
                        data=Bold(f"Login {self._login} already using"),
                        mark=DENIAL
                    )
                else:
                    self._login = login
                    await self._text_map['login'].update_text(data=Bold(login))
                    await self._text_map['feedback'].update_text(data=Italic("Login allowed"), mark=OK)


class Password(Markup):
    _strength_marks = {
        4: '🟢 Reliable',
        3: '🟡 Good',
        2: '🟠 Medium',
        1: '🔴 Bad',
        0: '⚠️ Terrible'
    }

    def __init__(self):
        super().__init__()
        self._password = None
        self._repeat_password = None
        self._hash = None

        self._header = 'Choose the password'
        self._text_map = {
            "password": CommonTexts.password(),
            "repeat_password": TextWidget(Bold("Repeat password: ")),
            "strength": TextWidget(Bold("Strength")),
            "warning": TextWidget(Bold("⚠️ Warning")),
            "suggestions": TextWidget(Bold("Suggestions")),
            "feedback": CommonTexts.feedback(),
        }
        self._markup_map = [
            {
                "accept": CommonButtons.accept("accept_password")
            },
            {
                "input_mode": ButtonWidget("🔄 Input mode", "mode_password"),
            },
            {
                "back": CommonButtons.back("sign_up")
            }
        ]

    @property
    def password(self):
        return '*' * len(self._password)

    @property
    def hash(self):
        return self._hash

    # async def password_input_state(self):
    #     await self._update_header('Choose the password')
    #
    # async def repeat_password_state(self):
    #     await self._update_header('Repeat the password')
    #
    # async def accepted_password_state(self):
    #     self._password = None

    async def update_password(self, password):
        self._hash = None
        if len(password) > PASSWORD_LENGTH:
            await self._text_map['warning'].update_text(data=f"Maximum password length is {PASSWORD_LENGTH} symbols")
        else:
            password_grade = zxcvbn(password)
            warning = password_grade['feedback'].get('warning')
            suggestions = password_grade['feedback'].get('suggestions')

            self._password = password
            await self._text_map['password'].update_text(data=self.password)
            await self._text_map['repeat_password'].reset()
            await self._text_map['strength'].update_text(data=self._strength_marks[password_grade['score']])
            warning = Bold(warning) if warning is not None else OK
            await self._text_map['warning'].update_text(data=warning)
            suggestions = Bold("\n" + "\n".join(suggestions)) if suggestions is not None else OK
            await self._text_map['suggestions'].update_text(data=suggestions)

    async def repeat_password(self, password):
        self._repeat_password = password
        if password != self._password:
            await self._text_map['password'].update_text(mark=DENIAL)
            await self._text_map['repeat_password'].update_text(data='*' * len(password), mark=DENIAL)
            await self._text_map['feedback'].update_text(data="Passwords not matched")
        else:
            await self._text_map['password'].update_text(mark=OK)
            await self._text_map['repeat_password'].update_text(data='*' * len(password), mark=OK)
            self._hash = pbkdf2_sha256.hash(password)


class SignUp(Markup):
    def __init__(self):
        super().__init__()
        self._nickname = Nickname()
        self._login = Login()
        self._password = Password()

        self._text_map = {
            "nickname": CommonTexts.nickname(),
            "login": CommonTexts.login(),
            "password": CommonTexts.password(),
            "feedback": CommonTexts.feedback(),
        }
        self._markup_map = [
            {
                "nickname": ButtonWidget("🪪 Change nickname", "sign_up_nickname"),
                "login": ButtonWidget("🆔 Change login", "sign_up_login"),
                "password": ButtonWidget("🔑 Change password", "sign_up_password")
            },
            {
                "accept": CommonButtons.accept("accept_sign_up")
            },
            {
                "back": CommonButtons.back("authorization")
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

    async def update_sign_in(self):
        nickname = "❔" if self._nickname.nickname is None else self._nickname.nickname
        login = "❔" if self._login.login is None else self._login.login
        password = "❔" if self._password.hash is None else self._password.password
        await self._text_map['nickname'].update_text(data=nickname)
        await self._text_map['login'].update_text(data=login)
        await self._text_map['password'].update_text(data=password)

    async def _reset(self):
        self._nickname = Nickname()
        self._login = Login()
        self._password = Password()
        for widget in self._text_map.values():
            widget.reset()

    async def accept_sign_up(self, user_id: int, session: ClientSession):
        if not all((self._nickname.nickname, self._login.login, self._password.hash)):
            await self._text_map['feedback'].update_text('All fields required')
            return

        async with session.post('/sign_up', data=jwt.encode(
            {
                "user_id": user_id,
                "nickname": self._nickname.nickname,
                "login": self._login.login,
                "password": self._password.hash,
            },
            os.getenv('JWT')
        )) as response:
            if response.status != 201:
                await self._text_map['feedback'].update_text((await response.json())['detail'])
                return

            await self._reset()
            await self._text_map['feedback'].update_text('Account created')

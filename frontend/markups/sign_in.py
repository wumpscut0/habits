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
            'nickname': TextWidget(Bold("🪪 Nickname")),
            'feedback': CommonTexts.feedback(),
        }
        self._markup_map = [
            {
                'accept': CommonButtons.accept('sign_in')
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
            "login": TextWidget('🆔 Login'),
            "feedback": CommonTexts.feedback()
        }
        self._markup_map = [
            {
                "accept": CommonButtons.accept('sign_in')
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
        self._hash = None
        # self._suggestions = None
        # self._warning = None

        self._header = 'Choose the password'
        self._text_map = [
            {"mark": "", "header": Bold("Password: "), "data": "❔"},
            {"mark": "", "header": Bold("Repeat password: "), "data": "❔"},
            {"mark": "", "header": Bold("Strength: "), "data": "❔"},
            {"mark": "⚠️", "header": Bold("Warning: "), "data": "✅"},
            {"mark": "", "header": Bold("Suggestions: "), "data": "✅"},
            {"mark": "", "header": Bold("Feedback: "), "data": "✅"},
        ]
        self._markup_map = [
            [
                {"mark": "✅ ", "text": "Accept", "callback_data": "accept_password"},
            ],
            [
                {"mark": "🔄 ", "text": "Input mode", "callback_data": "mode_password"},
            ],
            [
                {"mark": "⬇️ ", "text": "Back", "callback_data": "back_password"},
            ]
        ]

    @property
    def password(self):
        return '*' * len(self._password)

    @property
    def hash(self):
        return self._hash

    async def password_input_state(self):
        await self._update_header('Choose the password')

    async def repeat_password_state(self):
        await self._update_header('Repeat the password')

    async def accepted_password_state(self):
        self._password = None

    async def update_password(self, password):
        if len(password) > PASSWORD_LENGTH:
            await self._update_text({
                5: {'data': f"Maximum password length is {PASSWORD_LENGTH} symbols"},
            })
        else:
            grade = zxcvbn(password)
            warning = grade['feedback'].get('warning')
            suggestions = grade['feedback'].get('suggestions')

            self._password = password
            await self._update_text(
                {
                    0: {"mark": "", "data": self.password},
                    1: {"mark": "", "data": '❔'},
                    2: {"data": self._strength_marks[grade['score']]},
                    3: {"data": '✅' if not warning else Bold(warning)},
                    4: {"data": '✅' if not suggestions else Bold("\n" + "\n".join(suggestions))},
                }
            )

    async def repeat_password(self, password):
        if password != self._password:
            await self._update_text({
                0: {"mark": "❌ "},
                1: {"mark": "❌ ", "data": '*' * len(password)},
                5: {'data': "Passwords not matched"}
            })
        else:
            await self._update_text({
                0: {"mark": "✅ "},
                1: {"mark": "✅ ", "data": '*' * len(password)},
            })
            self._hash = pbkdf2_sha256.hash(password)


class SignIn(Markup):
    def __init__(self):
        super().__init__()
        self._nickname = Nickname()
        self._login = Login()
        self._password = Password()

        self._text_map = [
            {"mark": "", "header": Bold("Nickname: "), "data": "❔"},
            {"mark": "", "header": Bold("Login: "), "data": "❔"},
            {"mark": "", "header": Bold("Password: "), "data": "❔"},
        ]
        self._markup_map = [
            [
                {"mark": "", "text": "Change nickname", "callback_data": f"sign_in_nickname"},
                {"mark": "", "text": "Change login", "callback_data": f"sign_in_login"},
                {"mark": "", "text": "Change password", "callback_data": f"sign_in_password"},
            ],
            [
                {"mark": "✅ ", "text": "Accept", "callback_data": f"accept_sign_in"},
            ],
            [
                {"mark": "⬇️ ", "text": "Back", "callback_data": f"back_sign_in"}
            ],
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
        await self._update_text({
            0: {"data": "❔" if self._nickname.nickname is None else self._nickname.nickname},
            1: {"data": "❔" if self._login.login is None else self._login.login},
            2: {"data": "❔" if self._password.hash is None else self._password.password},
        })

    async def _reset(self):
        self._nickname = Nickname()
        self._login = Login()
        self._password = Password()
        await self._update_text({
            0: {"data": "❔"},
            1: {"data": "❔"},
            2: {"data": "❔"},
        })

    async def accept_sign_in(self, user_id: int):
        if all((self._nickname.nickname, self._login.login, self._password.hash)):
            async with aiohttp.ClientSession() as session:
                async with session.post(os.getenv('BACKEND') + '/sign_in', data=jwt.encode(
                    {
                        "user_id": user_id,
                        "nickname": self._nickname.nickname,
                        "login": self._login.login,
                        "password": self._password.hash,
                    },
                    os.getenv('JWT')
                )) as response:
                    if response.status != 201:
                        return {
                            "success": False,
                            "response": (await response.json())['detail']
                        }

            await self._reset()
            return {
                "success": True,
                "response": "Account created"
            }

        return {
            "success": False,
            "response": "All fields required"
        }



import re
from aiohttp import ClientSession
from config import *
from frontend.markups import Markup, CommonTexts, CommonButtons


class Login(Markup):
    def __init__(self):
        super().__init__()
        self._login = None

        self._header = 'Enter the login'
        self._text_map = {
            "login": CommonTexts.login(),
            "feedback": CommonTexts.feedback()
        }
        self._markup_map = [
            {
                "accept": CommonButtons.accept('open_sign_up')
            },
        ]

    @property
    def login(self):
        return self._login

    async def update_login(self, login, session: ClientSession):
        if not re.fullmatch(r'\w{3,10}', login, flags=re.I):
            await self._text_map['feedback'].update_text(
                data="Login must contains only latin symbols or signs '_' or digits.",
                mark=DENIAL
            )
        else:
            async with session.get(f'/verify_login/{login}') as response:
                if response.status == 409:
                    await self._text_map['feedback'].update_text(
                        data=f"Login {login} already using",
                        mark=DENIAL
                    )
                else:
                    self._login = login
                    await self._text_map['login'].update_text(data=login)
                    await self._text_map['feedback'].update_text(data="Login allowed", mark=OK)

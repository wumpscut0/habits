import os
import jwt
from aiogram.fsm.context import FSMContext
from aiohttp import ClientSession
from frontend import errors
from frontend.FSM import SignInState
from frontend.markups import Markup, ButtonWidget, CommonButtons, CommonTexts
from frontend.markups.profile import Profile


class SignIn(Markup):
    def __init__(self):
        super().__init__()
        self._login = None
        self._password = None

        self._profile = Profile()

        self._header = '🆔 Enter the login'
        self._default_header = self._header

        self._text_map = {
            "login": CommonTexts.login(),
            "password": CommonTexts.password(),
            "feedback": CommonTexts.feedback(),
        }
        self._markup_map = [
            {
                "sign_in": ButtonWidget("🔐 Sign in", "open_profile")
            },
            {
                "input_mode": CommonButtons.invert_mode("mode_sign_in"),
            },
            {
                "back": CommonButtons.back("open_authorization")
            }
        ]

    @property
    def profile(self):
        return self._profile

    async def invert_input_mode(self, state: FSMContext):
        if self._header == '🆔 Enter the login':
            self._header = "🔑 Enter the password"
            await state.set_state(SignInState.input_password)
        else:
            self._header = '🆔 Enter the login'
            await state.set_state(SignInState.input_login)

    async def input_login(self, login):
        await self._text_map['login'].update_text(data=login)
        self._login = login

    async def input_password(self, password):
        await self._text_map['password'].update_text(data=len(password) * '*')
        self._password = password

    async def try_sign_in(self, session: ClientSession):
        if not all((self._login, self._password)):
            await self._text_map['feedback'].update_text(data='All fields required')
            return False

        request = jwt.encode(
            {
                "login": self._login,
                "password": self._password,
            },
            os.getenv('JWT')
        )
        async with session.post(f'/sign_in', json={'jwt': request}) as response:
            data = await response.json()
            if response.status != 200:
                errors.error(data['detail'])
                await self._text_map['feedback'].update_text(data=data['detail'])
                return False
            await self._profile.merge_nickname(data['nickname'])
            return True

    async def reset(self, state: FSMContext):
        await state.set_state(SignInState.input_login)
        await self._reset()


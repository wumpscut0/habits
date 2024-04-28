import re

from aiogram.fsm.context import FSMContext
from aiohttp import ClientSession
from passlib.handlers.pbkdf2 import pbkdf2_sha256
from zxcvbn import zxcvbn
from config import MAX_PASSWORD_LENGTH, Emoji, MAX_EMAIL_LENGTH
from frontend.FSM import States
from frontend.markups import Markup, CommonButtons, ButtonWidget, DataTextWidget, TextWidget
from frontend.markups.interface import Interface
from frontend.utils import verify_email


class InputNewPassword(Markup):
    def __init__(self, interface: Interface):
        super().__init__(interface)
        self.password = None

    def _init_state(self):
        self._state = States.input_password

    def _init_text_map(self):
        self._text_map = {
            "action": TextWidget(f'{Emoji.KEY} Enter the new password'),
        }

    def _init_markup_map(self):
        self._markup_map = [
            {
                "back": CommonButtons.back("title_screen")
            }
        ]

    async def __call__(self, password: str, state: FSMContext):
        if len(password) > MAX_PASSWORD_LENGTH:
            await self.update_feedback(data=f"Maximum password length is {MAX_PASSWORD_LENGTH} symbols")
            await self.open(state)
        else:
            self.password = password
            await self._interface.repeat_password.open(state)


class RepeatNewPassword(Markup):
    def __init__(self, interface: Interface):
        super().__init__(interface)
        self.hash = None

    def _init_state(self):
        self._state = States.repeat_password

    def _init_text_map(self):
        self._text_map = {
            "action": TextWidget(f'{Emoji.KEY}{Emoji.KEY} Repeat password')
        }

    def _init_markup_map(self):
        self._markup_map = [
            {
                'back': CommonButtons.back("profile")
            }
        ]

    async def repeat_password(self, password, state):
        if password != self._interface.input_password.password:
            await self.update_feedback("Passwords not matched")
            await self._interface.input_password.open(state)
        else:
            self.hash = pbkdf2_sha256.hash(password)
            self._interface.input_password.password = None
            await self._interface.input_email.open(state)


class InputEmail(Markup):
    def __init__(self, interface: Interface):
        super().__init__(interface)
        self.email = None
        self.verify_code = None

    def _init_state(self):
        self._state = States.input_email

    def _init_text_map(self):
        self._text_map = {
            "action": TextWidget('Enter the email'),
        }

    def _init_markup_map(self):
        self._markup_map = [
            {
                "back": ButtonWidget('back', "profile")
            }
        ]

    async def input_email(self, email: str, state):
        if len(email) > MAX_EMAIL_LENGTH:
            await self.update_feedback(f'Max email length is {MAX_EMAIL_LENGTH} symbols.')
            await self.open(state)
        elif not re.fullmatch(r'\w+@\w+\.\w+', email, flags=re.I):
            await self.update_feedback('Allowable format is example@email.com')
            await self.open(state)
        else:
            self.email = email
            await self.update_feedback(f'Verify code sended on your email {email}')
            self.verify_code = await verify_email(email)
            await self._interface.input_verify_email_code.open(state)


class InputVerifyEmailCode(Markup):
    def __init__(self, interface: Interface):
        super().__init__(interface)

    def _init_state(self):
        self._state = States.input_verify_email_code

    def _init_text_map(self):
        self._text_map = {
            "action": TextWidget(f'Enter verify code sent on your email {self._interface.input_email.email}.')
        }

    def _init_markup_map(self):
        self._markup_map = [
            {
                "back_to_input_email": ButtonWidget(f'{Emoji.BACK} Change email', "input_email")
            }
        ]

    async def verify_email(self, verify_code, state):
        if verify_code != self._interface.input_email.verify_code:
            await self.update_feedback('Wrong verify code')
            await self.open(state)
        else:
            await self._interface.password_resume.open(state)


class PasswordResume(Markup):
    _strength_marks = {
        4: '🟢 Reliable',
        3: '🟡 Good',
        2: '🟠 Medium',
        1: '🔴 Bad',
        0: '⚠️ Terrible'
    }

    def __init__(self, interface: Interface):
        super().__init__(interface)

    def _init_text_map(self):
        self._text_map = {
            "info": TextWidget(f'{Emoji.DIAGRAM} Password grade'),
            "strength": DataTextWidget(f"{Emoji.SHIELD} Strength"),
            "warning": DataTextWidget(f"{Emoji.WARNING} Warning"),
            "suggestions": DataTextWidget(f"{Emoji.SHINE_STAR} Suggestions"),
        }

    def _init_markup_map(self):
        self._markup_map = [
            {
                "accept": CommonButtons.accept("update_password")
            },
            {
                "cancel": ButtonWidget(f'{Emoji.DENIAL} Cancel', "input_password")
            }
        ]

    async def open(self, state):
        password_grade = zxcvbn(self._interface.input_password.password)

        await self._text_map['strength'].update_text(data=self._strength_marks[password_grade['score']])

        warning = password_grade['feedback']['warning']
        if warning:
            await self._text_map['warning'].update_text(data=warning)

        suggestions = password_grade['feedback']['suggestions']
        if suggestions:
            suggestions = '\n'
            for n, suggestion in enumerate(suggestions, start=1):
                suggestions += f'{n}) {suggestion}'
            await self._text_map['suggestions'].update_text(data=suggestions)

        await super().open(state)
        await self.reset()

    async def update_password(self, session: ClientSession, state: FSMContext):
        async with session.patch('/update_password') as response:
            if response.status == 200:
                await self.update_feedback('Password updated')
                await self._interface.profile.open(state)
            elif response.status == 401:
                await self.abort(state)
            else:
                await self.handling_unexpected_error(state)


class SignInWithPassword(Markup):
    def __init__(self, interface: Interface):
        super().__init__(interface)

    def _init_state(self):
        self._state = States.sign_in_with_password

    def _init_text_map(self):
        self._text_map = {
            "info": TextWidget(f'{Emoji.KEY} Enter the password'),
            "feedback": CommonTexts.feedback()
        }

    def _init_markup_map(self):
        self._markup_map = [
            {
                "forgot": ButtonWidget(f'{Emoji.CYCLE} Reset password', 'reset_password')
            }
        ]

    async def sign_in_with_password(self, state: FSMContext, session: ClientSession, password: str):
        async with session.get('/sign_in', json={'telegram_id': self._interface.chat_id, "password": password}) as response:
            if response.status == 200:
                self._interface.token = (await response.json())['token']
                await self._interface.profile.open(state)
            else:
                await self._text_map['feedback'].update_text(data='Wrong password')
                await self.open(state)

    async def reset_password(self, state: FSMContext, session: ClientSession):
        async with session.patch('/reset_password', json={'telegram_id': self._interface.chat_id}) as response:
            if response == 200:
                await self._text_map['feedback'].update_text(data=f'New password sended on your email {await response.text()}')
            else:
                await self._text_map['feedback'].update_text(data="Internal server error")

            await self.open(state)

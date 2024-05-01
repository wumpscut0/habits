import re

from aiogram.fsm.context import FSMContext
from aiohttp import ClientSession
from passlib.handlers.pbkdf2 import pbkdf2_sha256
from zxcvbn import zxcvbn

from frontend.FSM import States
from frontend.markups import Mailing, MAX_PASSWORD_LENGTH, MAX_EMAIL_LENGTH
from frontend.markups.core import *


class AuthManager:
    def __init__(self, interface: Interface):
        self._interface = interface

        self.input_password = CreatePassword(interface)
        self.repeat_password = RepeatPassword(interface)
        self.resume_password = PasswordResume(interface)
        self.create_email = CreateEmail(interface)
        self.input_verify_email_code = InputVerifyEmailCode(interface)
        self.sign_in_with_password = SignInWithPassword(interface)

    async def reset_password(self, state: FSMContext, session: ClientSession):
        async with session.patch('/reset_password', json={'telegram_id': self._interface.chat_id}) as response:
            if response == 200:
                await self._interface.markup.update_feedback(f'New password sended on your email {await response.text()}')
            else:
                await self._interface.markup.handling_unexpected_error(state)

    async def update_password(self, session: ClientSession, state: FSMContext):
        await self._interface.auth_manager.resume_password.markup_map[0]['accept_password'].update_button(
            callback_data='update_password')
        await self.markup_map[0]['update_password'].update_button(text=f'{Emoji.KEY}{Emoji.UP} Update password')
        await self.markup_map[0]['delete_password'].update_button(active=True)
        async with session.patch('/update_password', json={
            "hash": self._interface.repeat_password.hash,
            "email": self._interface.input_email.email
        }) as response:
            if response.status == 200:
                await self.update_feedback(f'{Emoji.OK} Password and email updated')
                await self._interface.profile.open(state)
            elif response.status == 401:
                await self.abort_session(state)
            else:
                await self.handling_unexpected_error(state)

class CreatePassword(Markup):
    def __init__(self, interface: Interface):
        super().__init__(interface)
        self.password = None

    def _init_state(self):
        self._state = States.input_password

    def _init_text_map(self):
        self.text_map = {
            "action": TextWidget(f'{Emoji.KEY} Enter the password'),
        }

    def _init_markup_map(self):
        self._markup_map = [
            {
                "back": ButtonWidget(f"{Emoji.DENIAL} Cancel", callback_data='profile')
            }
        ]

    async def __call__(self, password: str, state: FSMContext):
        if len(password) > MAX_PASSWORD_LENGTH:
            await self.update_feedback(data=f"Maximum password length is {MAX_PASSWORD_LENGTH} symbols")
            await self.open(state)
        else:
            self.password = password
            await self._interface.auth_manager.repeat_password.open(state)


class RepeatPassword(Markup):
    def __init__(self, interface: Interface):
        super().__init__(interface)
        self.hash = None

    def _init_state(self):
        self._state = States.repeat_password

    def _init_text_map(self):
        self.text_map = {
            "action": TextWidget(f'{Emoji.KEY}{Emoji.KEY} Repeat the password')
        }

    def _init_markup_map(self):
        self._markup_map = [
            {
                "back": ButtonWidget(f"{Emoji.DENIAL} Cancel", callback_data='profile')
            }
        ]

    async def __call__(self, password, state):
        if password != self._interface.auth_manager.input_password.password:
            await self.update_feedback("Passwords not matched")
            await self._interface.auth_manager.input_password.open(state)
        else:
            self.hash = pbkdf2_sha256.hash(password)
            self._interface.auth_manager.input_password.password = None
            await self._interface.auth_manager.resume_password.open(state)
            
            
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
        self.text_map = {
            "info": TextWidget(f'{Emoji.DIAGRAM} Password grade'),
            "strength": DataTextWidget(f"{Emoji.SHIELD} Strength"),
            "warning": DataTextWidget(f"{Emoji.WARNING} Warning"),
            "suggestions": DataTextWidget(f"{Emoji.SHINE_STAR} Suggestions"),
        }

    def _init_markup_map(self):
        self._markup_map = [
            {
                "accept_password": ButtonWidget(f"{Emoji.OK + Emoji.KEY} Accept password", "create_email")
            },
            {
                "back": ButtonWidget(f'{Emoji.DENIAL} Cancel', "create_password")
            }
        ]

    async def open(self, state):
        password_grade = zxcvbn(self._interface.auth_manager.input_password.password)

        await self.text_map['strength'].update_text(data=self._strength_marks[password_grade['score']])

        warning = password_grade['feedback']['warning']
        if warning:
            await self.text_map['warning'].update_text(data=warning)

        suggestions = password_grade['feedback']['suggestions']
        if suggestions:
            suggestions = '\n'
            for n, suggestion in enumerate(suggestions, start=1):
                suggestions += f'{n}) {suggestion}'
            await self.text_map['suggestions'].update_text(data=suggestions)

        await super().open(state)
        await self.reset_text()


class CreateEmail(Markup):
    def __init__(self, interface: Interface):
        super().__init__(interface)
        self.email = None
        self.verify_code = None

    def _init_state(self):
        self._state = States.input_email

    def _init_text_map(self):
        self.text_map = {
            "action": TextWidget(f'{Emoji.ENVELOPE} Enter the email'),
        }

    def _init_markup_map(self):
        self._markup_map = [
            {
                "back": ButtonWidget(f'{Emoji.BACK} Back to profile', "profile")
            }
        ]

    async def __call__(self, email: str, state):
        if len(email) > MAX_EMAIL_LENGTH:
            await self.update_feedback(f'Max email length is {MAX_EMAIL_LENGTH} symbols.')
            await self.open(state)
        elif not re.fullmatch(r'\w+@\w+\.\w+', email, flags=re.I):
            await self.update_feedback('Allowable format is example@email.com')
            await self.open(state)
        else:
            self.email = email
            await self.update_feedback(f'Verify code sended on your email {email}')
            self.verify_code = await Mailing.verify_email(email)
            await self._interface.auth_manager.input_verify_email_code.open(state)


class InputVerifyEmailCode(Markup):
    def __init__(self, interface: Interface):
        super().__init__(interface)

    def _init_state(self):
        self._state = States.input_verify_email_code

    def _init_text_map(self):
        self.text_map = {
            "action": TextWidget(f'{Emoji.LOCK_AND_KEY} Enter verify code sent on your email {self._interface.auth_manager.input_email.email}.')
        }

    def _init_markup_map(self):
        self._markup_map = [
            {
                "back_to_input_email": ButtonWidget(f'{Emoji.BACK} Change email', "input_email")
            }
        ]

    async def __call__(self, verify_code, state, session: ClientSession):
        if verify_code != self._interface.auth_manager.create_email.verify_code:
            await self.update_feedback(f'{Emoji.DENIAL} Wrong verify code')
            await self.open(state)
        else:
            self._interface.auth_manager.create_email.verify_code = None
            await self._interface.auth_manager.resume_password.update_password(session, state)


class SignInWithPassword(Markup):
    def __init__(self, interface: Interface):
        super().__init__(interface)

    def _init_state(self):
        self._state = States.sign_in_with_password

    def _init_text_map(self):
        self.text_map = {
            "action": TextWidget(f'{Emoji.KEY} Enter the password'),
        }

    def _init_markup_map(self):
        self._markup_map = [
            {
                "reset_password": ButtonWidget(f'{Emoji.CYCLE} Reset password', 'reset_password')
            }
        ]

    async def sign_in_with_password(self, state: FSMContext, session: ClientSession, password: str):
        async with session.post('/sign_in', json={'telegram_id': self._interface.chat_id, "password": password}) as response:
            if response.status == 200:
                self._interface.token = (await response.json())['token']
                await self._interface.manprofile.open(state)
            elif response.status == 401:
                await self.update_feedback('Wrong password')
                await self.open(state)
            else:
                await self._interface.handling_unexpected_error(state)

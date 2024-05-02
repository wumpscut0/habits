import re
from datetime import datetime, timedelta

from aiogram.fsm.context import FSMContext
from aiohttp import ClientSession
from passlib.handlers.pbkdf2 import pbkdf2_sha256
from zxcvbn import zxcvbn

from frontend import scheduler, reset_verify_code
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

    async def update_password(self, session: ClientSession, state: FSMContext):
        async with (session.patch('/update_password', json={
            "hash": self._interface.storage['hash'],
            "email": self._interface.storage['email']
        }) as response):
            self._interface.storage.update({'hash': None, "email": None})

            if response.status == 200:
                if self._interface.basic_manager.options.markup_map['delete_password'].active:
                    feedback = f'{Emoji.OK} Password updated'
                else:
                    feedback = f'{Emoji.OK} Password and email updated'
                self._interface.feedback.data = feedback

                self._interface.auth_manager.resume_password.markup_map[
                    'accept_password'
                ].callback_data = 'update_password'

                self._interface.basic_manager.options.markup_map[
                    'update_password'
                ].text = f'{Emoji.KEY}{Emoji.UP} Update password'

                self._interface.basic_manager.options.markup_map['delete_password'].on()
                await self._interface.basic_manager.profile.open(state)
            elif response.status == 401:
                await self._interface.close_session(state)
            else:
                await self._interface.handling_unexpected_error(state)


class CreatePassword(TextMarkup):
    def __init__(self, interface: Interface):
        super().__init__(
            interface,
            text_map=TextMap(
                {
                    "action": TextWidget(f'{Emoji.KEY} Enter the password'),
                }
            ),
            markup_map=MarkupMap(
                [
                    {
                        "back": ButtonWidget(f"{Emoji.DENIAL} Cancel", callback_data='profile')
                    }
                ]
            ),
            state=States.input_password
        )

    async def __call__(self, password: str, state: FSMContext):
        if len(password) > MAX_PASSWORD_LENGTH:
            self._interface.feedback.data = f"Maximum password length is {MAX_PASSWORD_LENGTH} symbols"
            await self.open(state)
        else:
            self._interface.storage['password'] = password
            await self._interface.auth_manager.repeat_password.open(state)


class RepeatPassword(TextMarkup):
    def __init__(self, interface: Interface):
        super().__init__(
            interface,
            text_map=TextMap(
                {
                    "action": TextWidget(f'{Emoji.KEY}{Emoji.KEY} Repeat the password'),
                }
            ),
            markup_map=MarkupMap(
                [
                    {
                        "back": ButtonWidget(f"{Emoji.DENIAL} Cancel", callback_data='profile')
                    }
                ]
            ),
            state=States.repeat_password
        )

    async def __call__(self, password: str, state: FSMContext):
        if password != self._interface.storage['password']:
            self._interface.feedback.data = "Passwords not matched"
            await self._interface.auth_manager.input_password.open(state)
        else:
            self._interface.storage.update({
                "password_grade": zxcvbn(password),
                "hash": pbkdf2_sha256.hash(password),
                "password": None
            })
            await self._interface.auth_manager.resume_password.open(state)


class PasswordResume(TextMarkup):
    _strength_marks = {
        4: f'{Emoji.GREEN_CIRCLE} Reliable',
        3: f'{Emoji.YELLOW_CIRCLE} Good',
        2: f'{Emoji.ORANGE_CIRCLE} Medium',
        1: f'{Emoji.RED_CIRCLE} Bad',
        0: f'{Emoji.WARNING}️ Worst'
    }

    def __init__(self, interface: Interface):
        super().__init__(
            interface,
            text_map=TextMap(
                {
                    "info": TextWidget(f'{Emoji.DIAGRAM} Password grade'),
                    "strength": DataTextWidget(f"{Emoji.SHIELD} Strength"),
                    "warning": DataTextWidget(f"{Emoji.WARNING} Warning", active=False),
                    "suggestions": DataTextWidget(f"{Emoji.SHINE_STAR} Suggestions", active=False),
                }
            ),
            markup_map=MarkupMap(
                [
                    {
                        "accept_password": ButtonWidget(f"{Emoji.OK + Emoji.KEY} Accept password", "create_email")
                    },
                    {
                        "back": ButtonWidget(f'{Emoji.DENIAL} Cancel', "update_password")
                    }
                ]
            ),
        )

    async def open(self, state):
        password_grade = self._interface.storage['password_grade']

        self.text_map['strength'].data = self._strength_marks[password_grade['score']]

        warning = password_grade['feedback']['warning']
        if warning:
            self.text_map['warning'].data = warning
            self.text_map['warning'].on()

        suggestions = password_grade['feedback']['suggestions']
        if suggestions:
            suggestions = '\n'
            for n, suggestion in enumerate(suggestions, start=1):
                suggestions += f'{n}) {suggestion}'
            self.text_map['suggestions'].data = suggestions
            self.text_map['suggestions'].on()

        await super().open(state)
        self.text_map['warning'].off()
        self.text_map['suggestions'].off()


class CreateEmail(TextMarkup):
    def __init__(self, interface: Interface):
        super().__init__(
            interface,
            text_map=TextMap(
                {
                    "action": TextWidget(f'{Emoji.ENVELOPE} Enter the email'),
                }
            ),
            markup_map=MarkupMap(
                [
                    {
                        "back": ButtonWidget(f'{Emoji.BACK} Back to profile', "profile")
                    }
                ]
            ),
            state=States.input_email
        )

    async def __call__(self, email: str, state):
        if len(email) > MAX_EMAIL_LENGTH:
            self._interface.feedback.data = f'Max email length is {MAX_EMAIL_LENGTH} symbols.'
            await self.open(state)
        elif not re.fullmatch(r'\w+@\w+\.\w+', email, flags=re.I):
            self._interface.feedback.data = 'Allowable format is example@email.com'
            await self.open(state)
        else:
            self._interface.feedback.data = f'Verify code sended on your email {email}'
            scheduler.add_job(reset_verify_code, "date", (self._interface,),
                              run_date=datetime.now() + timedelta(minutes=5))
            self._interface.storage.update({
                "verify_code": await Mailing.verify_email(email),
                "email": email
            })
            await self._interface.auth_manager.input_verify_email_code.open(state)


class InputVerifyEmailCode(TextMarkup):
    def __init__(self, interface: Interface):
        super().__init__(
            interface,
            text_map=TextMap(
                {
                    "action": TextWidget(f'{Emoji.LOCK_AND_KEY} Enter verify code sent on your email'
                                         f' {self._interface.storage["email"]}.')
                }
            ),
            markup_map=MarkupMap(
                [
                    {
                        "back": ButtonWidget(f'{Emoji.BACK} Change email', "input_email")
                    }
                ]
            ),
            state=States.input_verify_email_code
        )

    async def __call__(self, verify_code, state, session: ClientSession):
        if self._interface.storage['verify_code'] is None:
            self._interface.feedback.data = f"Verify code expired"
            await self._interface.auth_manager.create_email.open(state)
        elif verify_code != self._interface.storage['verify_code']:
            self._interface.feedback.data = f'{Emoji.DENIAL} Wrong verify code'
            await self.open(state)
        else:
            self._interface.storage["verify_code"] = None
            await self._interface.auth_manager.update_password(session, state)


class SignInWithPassword(TextMarkup):
    def __init__(self, interface: Interface):
        super().__init__(
            interface,
            text_map=TextMap(
                {
                    "action": TextWidget(f'{Emoji.KEY} Enter the password'),
                }
            ),
            markup_map=MarkupMap(
                [
                    {
                        "reset_password": ButtonWidget(f'{Emoji.CYCLE} Reset password', 'reset_password')
                    }
                ]
            ),
            state=States.sign_in_with_password
        )

    async def __call__(self, state: FSMContext, session: ClientSession, password: str):
        async with session.post('/sign_in',
                                json={'telegram_id': self._interface.chat_id, "password": password}) as response:
            if response.status == 200:
                self._interface.token = (await response.json())['token']
                await self._interface.basic_manager.profile.open(state)
            elif response.status == 401:
                self._interface.feedback.data = 'Wrong password'
                await self.open(state)
            else:
                await self._interface.handling_unexpected_error(state)

    async def reset_password(self, state: FSMContext, session: ClientSession):
        async with session.patch('/reset_password', json={'telegram_id': self._interface.chat_id}) as response:
            if response == 200:
                self._interface.feedback.data = f'New password sent on your email {await response.text()}'
                await self.open(state)
            else:
                await self._interface.handling_unexpected_error(state)

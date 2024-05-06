import re
from datetime import datetime, timedelta

from aiogram.fsm.context import FSMContext
from aiohttp import ClientSession
from apscheduler.triggers.cron import CronTrigger
from passlib.handlers.pbkdf2 import pbkdf2_sha256
from zxcvbn import zxcvbn

from frontend import Emoji, scheduler, reset_verify_code
from frontend.FSM import States
from frontend.markups import Mailing, MAX_EMAIL_LENGTH, MAX_PASSWORD_LENGTH
from frontend.markups.core import *


class BasicManager:
    def __init__(self, interface: Interface):
        self._interface = interface
        self.title_screen = TitleScreen(interface)
        self.authorization_with_password = AuthorizationWithPassword(interface)

        self.profile = Profile(interface)
        self.options = Options(interface)
        self.input_password = CreatePassword(interface)
        self.repeat_password = RepeatPassword(interface)
        self.resume_password = PasswordResume(interface)
        self.input_email = CreateEmail(interface)
        self.input_verify_email_code = InputVerifyEmailCode(interface)
        self.change_notification_hour = ChangeNotificationsHour(interface)
        self.change_notification_minute = ChangeNotificationsMinute(interface)


class TitleScreen(TextMarkup):
    def __init__(self, interface: Interface):
        super().__init__(
            interface,
            TextMap(
                {
                    "info": TextWidget(f"{Emoji.BRAIN} Psychological service"),
                }
            ),
            MarkupMap(
                [
                    {
                        "sign_in": ButtonWidget(text=f'{Emoji.DOOR}', callback_data='authorization'),
                    },
                    {
                        "notifications": ButtonWidget(
                            text="Notifications",
                            callback_data="invert notifications",
                            mark=Emoji.BELL
                        ),
                    },
                ]
            )
        )

    async def authorization(self, session: ClientSession, state: FSMContext):
        async with session.post('/sign_in', json={'telegram_id': self._interface.chat_id}) as response:
            if response.status == 400:
                await self._interface.basic_manager.authorization_with_password.open(state)
            elif response.status == 200:
                await self._interface.basic_manager.profile.open(state)
            else:
                self._interface.feedback.data = 'Internal server error'
                await self.open(state)

    async def invert_notifications(self, session: ClientSession, state: FSMContext):
        async with session.patch('/invert_notifications', json={'telegram_id': self._interface.chat_id}) as response:
            response = await response.text()
        if response == '1':
            self.markup_map["notifications"].mark = Emoji.BELL
        elif response == '0':
            self.markup_map["notifications"].mark = Emoji.NOT_BELL
        else:
            await self.text_map['feedback'].update_text('Internal server error')

        await self.open(state)


class Profile(TextMarkup):
    def __init__(self, interface: Interface):
        super().__init__(
            interface,
            TextMap(
                {
                    "hello": DataTextWidget(header='Hello', sep=', '),
                }
            ),
            MarkupMap(
                [
                    {
                        "targets": ButtonWidget(text=f"{Emoji.DIAGRAM} Targets", callback_data="targets_control"),
                    },
                    {
                        "options": ButtonWidget(text=f'{Emoji.GEAR️} Options', callback_data="options")
                    },
                    {
                        "title_screen": ButtonWidget(text=f'{Emoji.BACK} Exit', callback_data="title_screen")
                    }
                ]
            )
        )

    async def open(self, state, **kwargs):
        self.text_map['hello'].data = self._interface.first_name
        await super().open(state)


class Options(TextMarkup):
    def __init__(self, interface: Interface):
        super().__init__(
            interface,
            TextMap(
                {
                    "notification_time": DataTextWidget(header=f"{Emoji.BELL + Emoji.CLOCK} Notification time")
                }
            ),
            MarkupMap(
                [
                    {
                        "update_password": ButtonWidget(
                            callback_data="update_password"
                        ),
                        "delete_password": ButtonWidget(
                            text=f"{Emoji.KEY + Emoji.DENIAL} Remove password",
                            callback_data="delete_password",
                            active=False
                        ),
                    },
                    {
                        "notifications": ButtonWidget(
                            text=f"{Emoji.BELL + Emoji.CLOCK} Change notification time",
                            callback_data="change_notification_time"
                        )
                    }
                ]
            )
        )

    async def open(self, state, **kwargs):
        async with kwargs['session'].get(f'/notification_time') as response:
            time_ = await response.json()
            self.text_map["notification_time"].data = f"{time_['hour']}:{time_['minute']}"

        if self.markup_map["delete_password"].active:
            self.markup_map['update_password'].text = f'{Emoji.KEY}{Emoji.UP} Update password'
        else:
            self.markup_map["update_password"].text = f"{Emoji.KEY}{Emoji.PLUS} Add password"

        await super().open(state)

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

                self._interface.basic_manager.options.markup_map['delete_password'].on()
                await self._interface.basic_manager.profile.open(state)
            elif response.status == 401:
                await self._interface.close_session(state)
            else:
                await self._interface.handling_unexpected_error(state)

    async def delete_password(self, state: FSMContext, session: ClientSession):
        async with session.delete("delete_password") as response:
            if response.status == 200:
                self.markup_map["delete_password"].off()
                self._interface.feedback.data = "password deleted"
                await self.open(state)
            elif response.status == 401:
                await self._interface.close_session(state)
            else:
                await self._interface.handling_unexpected_error(state)

    async def update_notifications_time(self, session: ClientSession, state: FSMContext):
        hour = self._interface.storage["hour"]
        minute = self._interface.storage["minute"]

        async with session.patch('/notification_time', json={"hour": hour, "minute": minute}) as response:
            if response.status == 200:
                self.text_map["notification_time"].data = f"{hour}:{minute}"
                scheduler.modify_job(self._interface.chat_id, trigger=CronTrigger(hour=hour, minute=minute))
                await self.open(state)
            elif response.status == 401:
                await self._interface.close_session(state)
            else:
                await self._interface.handling_unexpected_error(state)
        self._interface.storage.update({"hour": None, "minute": None})


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
                        "back": ButtonWidget(text=f"{Emoji.DENIAL} Cancel", callback_data='profile')
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
            await self._interface.basic_manager.repeat_password.open(state)


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
                        "back": ButtonWidget(text=f"{Emoji.DENIAL} Cancel", callback_data='profile')
                    }
                ]
            ),
            state=States.repeat_password
        )

    async def __call__(self, password: str, state: FSMContext):
        if password != self._interface.storage['password']:
            self._interface.feedback.data = "Passwords not matched"
            await self._interface.basic_manager.input_password.open(state)
        else:
            self._interface.storage.update({
                "password_grade": zxcvbn(password),
                "hash": pbkdf2_sha256.hash(password),
                "password": None
            })
            await self._interface.basic_manager.resume_password.open(state)


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
                    "strength": DataTextWidget(header=f"{Emoji.SHIELD} Strength"),
                    "warning": DataTextWidget(header=f"{Emoji.WARNING} Warning", active=False),
                    "suggestions": DataTextWidget(header=f"{Emoji.SHINE_STAR} Suggestions", active=False),
                }
            ),
            markup_map=MarkupMap(
                [
                    {
                        "accept_password": ButtonWidget(
                            text=f"{Emoji.OK + Emoji.KEY} Accept password",
                            callback_data="create_email"
                        )
                    },
                    {
                        "back": ButtonWidget(text=f'{Emoji.DENIAL} Cancel', callback_data="update_password")
                    }
                ]
            ),
        )

    async def open(self, state, **kwargs):
        if self._interface.basic_manager.options.markup_map['delete_password'].active:
            self.markup_map['accept_password'].callback_data = 'update_password'

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
                        "back": ButtonWidget(text=f'{Emoji.BACK} Back to profile', callback_data="profile")
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
            await self._interface.basic_manager.input_verify_email_code.open(state)


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
                        "back": ButtonWidget(text=f'{Emoji.BACK} Change email', callback_data="input_email")
                    }
                ]
            ),
            state=States.input_verify_email_code
        )

    async def __call__(self, verify_code, state, session: ClientSession):
        if self._interface.storage['verify_code'] is None:
            self._interface.feedback.data = f"Verify code expired"
            await self._interface.basic_manager.create_email.open(state)
        elif verify_code != self._interface.storage['verify_code']:
            self._interface.feedback.data = f'{Emoji.DENIAL} Wrong verify code'
            await self.open(state)
        else:
            self._interface.storage["verify_code"] = None
            await self._interface.basic_manager.update_password(session, state)


class NotificationHourCallbackData(CallbackData):
    hour: int


class ChangeNotificationsHour(TextMarkup):
    def __init__(self, interface: Interface):
        super().__init__(
            interface,
            TextMap(
                {
                    "info": TextWidget(f"{Emoji.CLOCK} Choose notification hour")
                }
            ),
            MarkupMap(
                [
                    {
                        str(hour): ButtonWidget(
                            callback_data=NotificationHourCallbackData(hour=hour)
                        ) for hour in range(start, start + 8)
                    }
                    for start in range(0, 24, 8)
                ] + [
                    {
                        "back": ButtonWidget(text=f"{Emoji.BACK} Cancel", callback_data='options')
                    }
                ]
            )
        )

    def __call__(self, hour: int, state):
        self._interface.storage["hour"] = hour
        self._interface.basic_manager.change_notification_minute.open(state)


class NotificationMinuteCallbackData(CallbackData):
    minute: int


class ChangeNotificationsMinute(TextMarkup):
    def __init__(self, interface: Interface):
        super().__init__(
            interface,
            TextMap(
                {
                    "info": TextWidget(f"{Emoji.CLOCK} Choose notification minute")
                }
            ),
            MarkupMap(
                [
                    {
                        str(hour): ButtonWidget(
                            callback_data=NotificationMinuteCallbackData(hour=hour)
                        ) for hour in range(start, start + 10)
                    }
                    for start in range(0, 60, 10)
                ] + [
                    {
                        "back": ButtonWidget(text=f"{Emoji.BACK} Cancel", callback_data='options')
                    }
                ]
            )
        )

    async def __call__(self, minute: int, state: FSMContext, session: ClientSession):
        self._interface.storage["minute"] = minute
        self._interface.basic_manager.options.update_notifications_time(session, state)


class AuthorizationWithPassword(TextMarkup):
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
                        "reset_password": ButtonWidget(
                            text=f'{Emoji.CYCLE} Reset password',
                            callback_data='reset_password'
                        )
                    }
                ]
            ),
            state=States.sign_in_with_password
        )

    async def __call__(self, state: FSMContext, session: ClientSession, password: str):
        async with session.post('/sign_in', json={
            'telegram_id': self._interface.chat_id, "password": password
        }) as response:
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

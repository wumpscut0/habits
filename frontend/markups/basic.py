import re
from datetime import datetime, timedelta, UTC

from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiohttp import ClientSession
from apscheduler.triggers.cron import CronTrigger
from passlib.handlers.pbkdf2 import pbkdf2_sha256
from zxcvbn import zxcvbn

from frontend.bot.FSM import States
from frontend.markups.core import TextMarkup, TextMap, TextWidget, MarkupMap, ButtonWidget, DataTextWidget

from frontend.utils import Emoji, config, get_service_key, encode_jwt
from frontend.utils.mailing import Mailing
from frontend.utils.scheduler import scheduler, reset_verify_code

MAX_EMAIL_LENGTH = config.getint('limitations', 'MAX_EMAIL_LENGTH')
MAX_NAME_LENGTH = config.getint('limitations', 'MAX_NAME_LENGTH')
MAX_DESCRIPTION_LENGTH = config.getint('limitations', 'MAX_DESCRIPTION_LENGTH')
MAX_PASSWORD_LENGTH = config.getint('limitations', "MAX_PASSWORD_LENGTH")
MIN_BORDER_RANGE = config.getint('limitations', "MIN_BORDER_RANGE")
MAX_BORDER_RANGE = config.getint('limitations', "MAX_BORDER_RANGE")
STANDARD_BORDER_RANGE = config.getint('limitations', "STANDARD_BORDER_RANGE")


class BasicManager:
    def __init__(self, interface):
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
    def __init__(self, interface):
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
                        "sign_in": ButtonWidget(text=f'{Emoji.DOOR} Sign in', callback_data='authorization'),
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
                self._interface.token = await response.text()
                await self._interface.basic_manager.profile.open(state)
            else:
                await self._interface.handling_unexpected_error(state, response)

    async def invert_notifications(self, session: ClientSession, state: FSMContext):
        token = await encode_jwt({"telegram_id": self._interface.chat_id})
        async with session.patch(f'/invert_notifications/{token}') as response:
            content = await response.text()
        if content == '1':
            self.markup_map["notifications"].mark = Emoji.BELL
            async with session.get(f"/is_all_done/{await self._interface.user_encode_id()}") as response_:
                if await response_.text() == "0":
                    await self._interface.notification_on(session)
            await self.open(state)
        elif content == '0':
            await self._interface.notification_off()
            self.markup_map["notifications"].mark = Emoji.NOT_BELL
            await self.open(state)
        else:
            await self._interface.handling_unexpected_error(state, response)


class Profile(TextMarkup):
    def __init__(self, interface):
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
                        "options": ButtonWidget(text=f'{Emoji.GEAR} Options', callback_data="options")
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
    def __init__(self, interface):
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
                    },
                    {
                        "back": ButtonWidget(
                            text=f"{Emoji.BACK} Back",
                            callback_data="profile"
                        )
                    }
                ]
            )
        )

    async def open(self, state, **kwargs):
        async with kwargs['session'].get(f'/notification_time/{await self._interface.user_encode_id()}') as response:
            time_ = await response.json()
            minute = str(time_['minute'])
            minute = "0" + minute if len(minute) < 2 else minute
            self.text_map["notification_time"].data = f"{time_['hour']}:{minute}"

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
                await self._interface.update_feedback(feedback)

                self._interface.basic_manager.options.markup_map['delete_password'].on()
                await self._interface.basic_manager.profile.open(state)
            elif response.status == 401:
                await self._interface.close_session(state)
            else:
                await self._interface.handling_unexpected_error(state, response)

    async def delete_password(self, state: FSMContext, session: ClientSession):
        async with session.delete("delete_password") as response:
            if response.status == 200:
                self.markup_map["delete_password"].off()
                await self._interface.update_feedback("password deleted")
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
                await self._interface.update_notification_time()
                await self.open(state, session=session)
            elif response.status == 401:
                await self._interface.close_session(state)
            else:
                await self._interface.handling_unexpected_error(state, response)

        self._interface.storage.update({"hour": None, "minute": None})


class CreatePassword(TextMarkup):
    def __init__(self, interface):
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
                        "back": ButtonWidget(text=f"{Emoji.DENIAL} Cancel", callback_data='options')
                    }
                ]
            ),
            state=States.input_password
        )

    async def __call__(self, password: str, state: FSMContext):
        if len(password) > MAX_PASSWORD_LENGTH:
            await self._interface.update_feedback(f"Maximum password length is {MAX_PASSWORD_LENGTH} symbols")
            await self.open(state)
        else:
            self._interface.storage['password'] = password
            await self._interface.basic_manager.repeat_password.open(state)


class RepeatPassword(TextMarkup):
    def __init__(self, interface):
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
                        "back": ButtonWidget(text=f"{Emoji.DENIAL} Cancel", callback_data='options')
                    }
                ]
            ),
            state=States.repeat_password
        )

    async def __call__(self, password: str, state: FSMContext):
        if password != self._interface.storage['password']:
            await self._interface.update_feedback("Passwords not matched")
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

    def __init__(self, interface):
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
            suggestions_ = '\n'
            for n, suggestion in enumerate(suggestions, start=1):
                suggestions_ += f'{n}) {suggestion}'
            self.text_map['suggestions'].data = suggestions_
            self.text_map['suggestions'].on()

        await super().open(state)
        await self.text_map['warning'].reset()
        self.text_map['warning'].off()
        await self.text_map['suggestions'].reset()
        self.text_map['suggestions'].off()
        await self._interface.update_interface_in_redis(state)


class CreateEmail(TextMarkup):
    def __init__(self, interface):
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
                        "back": ButtonWidget(text=f'{Emoji.DENIAL} Cancel', callback_data="options")
                    }
                ]
            ),
            state=States.input_email
        )

    async def __call__(self, email: str, state):
        if len(email) > MAX_EMAIL_LENGTH:
            await self._interface.update_feedback(f'Max email length is {MAX_EMAIL_LENGTH} symbols.')
            await self.open(state)
        elif not re.fullmatch(r'\w+@\w+\.\w+', email, flags=re.I):
            await self._interface.update_feedback('Allowable format is example@email.com')
            await self.open(state)
        else:
            await self._interface.update_feedback(f'Verify code sended on your email {email}')
            scheduler.add_job(reset_verify_code, "date", (self._interface,),
                              run_date=datetime.now(tz=UTC) + timedelta(minutes=5))
            self._interface.storage.update({
                "verify_code": await Mailing.verify_email(email),
                "email": email
            })
            await self._interface.basic_manager.input_verify_email_code.open(state)


class InputVerifyEmailCode(TextMarkup):
    def __init__(self, interface):
        super().__init__(
            interface,
            text_map=TextMap(
                {
                    "action": TextWidget()
                }
            ),
            markup_map=MarkupMap(
                [
                    {
                        "back": ButtonWidget(text=f'{Emoji.BACK} Change email', callback_data="create_email")
                    }
                ]
            ),
            state=States.input_verify_email_code
        )

    async def open(self, state, **kwargs):
        self.text_map["action"].text = (f'{Emoji.LOCK_AND_KEY} Enter verify code sent on your email'
                                        f' {self._interface.storage.get("email")}.')
        await super().open(state)

    async def __call__(self, verify_code, state, session: ClientSession):
        if self._interface.storage['verify_code'] is None:
            await self._interface.update_feedback(f"Verify code expired")
            await self._interface.basic_manager.create_email.open(state)
        elif verify_code != self._interface.storage['verify_code']:
            await self._interface.update_feedback(f'{Emoji.DENIAL} Wrong verify code')
            await self.open(state)
        else:
            self._interface.storage["verify_code"] = None
            await self._interface.basic_manager.options.update_password(session, state)


class NotificationHourCallbackData(CallbackData, prefix="notification_hour"):
    hour: int


class ChangeNotificationsHour(TextMarkup):
    def __init__(self, interface):
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
                            text=str(hour),
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

    async def __call__(self, hour: int, state):
        self._interface.storage["hour"] = hour
        await self._interface.basic_manager.change_notification_minute.open(state)


class NotificationMinuteCallbackData(CallbackData, prefix="notification_minute"):
    minute: int


class ChangeNotificationsMinute(TextMarkup):
    def __init__(self, interface):
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
                        str(minute): ButtonWidget(
                            text=str(minute),
                            callback_data=NotificationMinuteCallbackData(minute=minute)
                        ) for minute in range(start, start + 8)
                    }
                    for start in range(0, 56, 8)
                ] + [
                    {
                        str(minute): ButtonWidget(
                            text=str(minute),
                            callback_data=NotificationMinuteCallbackData(minute=minute)
                        ) for minute in range(56, 60)
                    }
                ] + [
                    {
                        "back": ButtonWidget(text=f"{Emoji.BACK} Cancel", callback_data='options')
                    }
                ]
            )
        )

    async def __call__(self, minute: int, state: FSMContext, session: ClientSession):
        self._interface.storage["minute"] = minute
        await self._interface.basic_manager.options.update_notifications_time(session, state)


class AuthorizationWithPassword(TextMarkup):
    def __init__(self, interface):
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
                self._interface.token = await response.text()
                await self._interface.basic_manager.profile.open(state)
            elif response.status == 401:
                await self._interface.update_feedback('Wrong password')
                await self.open(state)
            else:
                await self._interface.handling_unexpected_error(state)

    async def reset_password(self, state: FSMContext, session: ClientSession):
        async with session.patch('/reset_password', json={'telegram_id': self._interface.chat_id}) as response:
            if response == 200:
                await self._interface.update_feedback(f'New password sent on your email {await response.text()}')
                await self.open(state)
            else:
                await self._interface.handling_unexpected_error(state)

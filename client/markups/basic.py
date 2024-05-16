import re

from aiogram.filters.callback_data import CallbackData
from passlib.handlers.pbkdf2 import pbkdf2_sha256
from zxcvbn import zxcvbn

from client.bot import bot
from client.bot.FSM import States
from client.markups.core import TextMarkup, TextMap, TextWidget, MarkupMap, ButtonWidget, DataTextWidget

from client.utils import Emoji, config
from client.utils.mailing import Mailing

MAX_EMAIL_LENGTH = config.getint('limitations', 'MAX_EMAIL_LENGTH')
MAX_NAME_LENGTH = config.getint('limitations', 'MAX_NAME_LENGTH')
MAX_DESCRIPTION_LENGTH = config.getint('limitations', 'MAX_DESCRIPTION_LENGTH')
MAX_PASSWORD_LENGTH = config.getint('limitations', "MAX_PASSWORD_LENGTH")
MIN_BORDER_RANGE = config.getint('limitations', "MIN_BORDER_RANGE")
MAX_BORDER_RANGE = config.getint('limitations', "MAX_BORDER_RANGE")
STANDARD_BORDER_RANGE = config.getint('limitations', "STANDARD_BORDER_RANGE")
VERIFY_CODE_EXPIRATION = config.getint("limitations", "VERIFY_CODE_EXPIRATION")


class TitleScreen(TextMarkup):
    def __init__(self):
        super().__init__(
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

    async def open(self, **kwargs):
        response = await self._interface.get_user()

        if response is not None:
            user = await response.json()
            if user["notification"]:
                self.markup_map["notifications"].mark = Emoji.BELL
            else:
                self.markup_map["notifications"].mark = Emoji.NOT_BELL
        else:
            self.markup_map["notifications"].mark = Emoji.RED_QUESTION

        if kwargs.get('new_session'):
            user_id = self._interface.chat_id
            message = await bot.send_message(
                chat_id=user_id,
                text=await self.text,
                reply_markup=await self.markup
            )

            storage.set(str(user_id), message.message_id)
            self._interface.update_interface_in_redis()
        else:
            await super().open()

    async def invert_notifications(self):
        async with self._interface.session.patch(
                "/users/notifications/invert",
                json={"user_id": self._interface.chat_id},
                headers={"Authorization": storage.get("service_key")}
        ) as response:
            response = await self._interface.response_middleware(response)
            if response == 401:
                await self.invert_notifications()


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

    async def open(self):
        storage.get(f"first_name:{self._interface.chat_id}")
        await super().open()


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
                        "input_password": ButtonWidget(
                            callback_data="input_password"
                        ),
                        "delete_password": ButtonWidget(
                            text=f"{Emoji.KEY + Emoji.DENIAL} Remove password",
                            callback_data="delete_password",
                            active=False
                        ),
                    },
                    {
                        "input_email": ButtonWidget(
                            callback_data='input_email',
                        ),
                        "delete_email": ButtonWidget(
                            text=f"{Emoji.ENVELOPE + Emoji.DENIAL} Remove email",
                            callback_data="delete_email",
                            active=False
                        )
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

    async def open(self):
        response = await self._interface.get_user()
        if response is not None:
            user = await response.json()
            time_ = user["notifications_time"]
            minute = str(time_['minute'])
            minute = "0" + minute if len(minute) < 2 else minute
            self.text_map["notification_time"].data = f"{time_['hour']}:{minute}"

            if user["hash"]:
                self.markup_map['delete_password'].on()
                self.markup_map['input_password'].text = f'{Emoji.KEY + Emoji.UP} Change password'
            else:
                self.markup_map['delete_password'].off()
                self.markup_map["input_password"].text = f"{Emoji.KEY + Emoji.PLUS} Add password"

            if user["email"]:
                self.markup_map['delete_email'].on()
                self.markup_map['input_email'].text = f'{Emoji.ENVELOPE + Emoji.UP} Change email'
            else:
                self.markup_map['delete_email'].off()
                self.markup_map["input_email"].text = f"{Emoji.ENVELOPE + Emoji.PLUS} Add email"

            await super().open()

    async def update_password(self):
        async with self._interface.session.put(
            f"/users/password",
            json={
                "user_id": self._interface.chat_id,
                "hash": storage.get(f"hash:{self._interface.chat_id}"),
            },
            headers={"Authorization": storage.get("service_key")}
        ) as response:
            response = self._interface.response_middleware(response)
            if response is not None:
                await self._interface.update_feedback(f'Password updated', type_="info")
                await self._interface.basic_manager.title_screen.open()

    async def delete_password(self):
        async with self._interface.session.delete(
                f"/users/password",
                headers={"Authorization": self._interface.token}
        ) as response:
            response = self._interface.response_middleware(response)
            if response is not None:
                self.markup_map["delete_password"].off()
                await self._interface.update_feedback("password deleted")
                await self.open()

    async def update_email(self):
        async with self._interface.session.put(
            f"/users/email",
            json={
                "email": storage.get(f"email:{self._interface.chat_id}"),
            },
            headers={"Authorization": self._interface.token}
        ) as response:
            response = self._interface.response_middleware(response)
            if response is not None:
                await self._interface.update_feedback(f'Email updated', type_="info")
                await self.open()

    async def delete_email(self):
        async with self._interface.session.delete(
                f"/users/email",
                headers={"Authorization": self._interface.token}
        ) as response:
            response = self._interface.response_middleware(response)
            if response is not None:
                self.markup_map["delete_email"].off()
                await self._interface.update_feedback("email deleted")
                await self.open()

    async def update_notifications_time(self):
        hour = storage.get(f"hour:{self._interface.chat_id}")
        minute = storage.get(f"minute:{self._interface.chat_id}")

        async with self._interface.session.put(
                "/users/notifications",
                json={"hour": hour, "minute": minute},
                headers={"Authorization": self._interface.token}
        ) as response:
            response = self._interface.response_middleware(response)
            if response is not None:
                self.text_map["notification_time"].data = f"{hour}:{minute}"
                await self._interface.refresh_notifications()
                await self.open()


class InputPassword(TextMarkup):
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

    async def __call__(self, password: str):
        if len(password) > MAX_PASSWORD_LENGTH:
            await self._interface.update_feedback(f"Maximum password length is {MAX_PASSWORD_LENGTH} symbols")
            await self.open()
        else:
            storage.set(f'password:{self._interface.chat_id}', password)
            await self._interface.basic_manager.repeat_password.open()


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

    async def __call__(self, password: str):
        if password != storage.get(f"password:{self._interface.chat_id}"):
            await self._interface.update_feedback("Passwords not matched")
            await self._interface.basic_manager.input_password.open()
        else:
            storage.set(f"password_grade:{self._interface.chat_id}", zxcvbn(password))
            storage.set(f"hash:{self._interface.chat_id}", pbkdf2_sha256.hash(password))
            await self._interface.basic_manager.resume_password.open()


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
                            callback_data="update_password"
                        )
                    },
                    {
                        "back": ButtonWidget(text=f'{Emoji.CYCLE} Change password', callback_data="input_password")
                    }
                ]
            ),
        )

    async def open(self):
        password_grade = storage.get(f'password_grade:{self._interface.chat_id}')

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

        await super().open()
        self.text_map['warning'].off()
        self.text_map['suggestions'].off()
        await self._interface.update_interface_in_redis()


class InputEmail(TextMarkup):
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

    async def __call__(self, email: str):
        if len(email) > MAX_EMAIL_LENGTH:
            await self._interface.update_feedback(f'Max email length is {MAX_EMAIL_LENGTH} symbols.')
            await self.open()
        elif not re.fullmatch(r'[a-zA-Z0-9]+@[a-zA-Z]+\.[a-zA-Z]', email, flags=re.I):
            await self._interface.update_feedback('Allowable format is example@email.com', type_="error")
            await self.open()
        else:
            await self._interface.temp_message("Sending...")
            verify_code = await Mailing.verify_email(email)
            if verify_code is not None:
                await self._interface.update_feedback(f"verify code sent on email:"
                                                      f" {email}.",
                                                      type_='info')
                storage.setex(f"verify_email_code:{self._interface.chat_id}", VERIFY_CODE_EXPIRATION, verify_code)
                storage.set(f"email:{self._interface.chat_id}", email)
                await self._interface.basic_manager.input_verify_email_code.open()
            else:
                await self._interface.update_feedback(f"Email {email} not found", type_="error")
                await self.open()


class InputVerifyEmailCode(TextMarkup):
    def __init__(self, interface):
        super().__init__(
            interface,
            text_map=TextMap(
                {
                    "action": TextWidget(
                        text=f'{Emoji.LOCK_AND_KEY} Enter verify code'
                    )
                }
            ),
            markup_map=MarkupMap(
                [
                    {
                        "back": ButtonWidget(text=f'{Emoji.CYCLE} Change email', callback_data="create_email")
                    }
                ]
            ),
            state=States.input_verify_email_code
        )

    async def __call__(self, verify_code):
        await self._interface.temp_message()
        verify_code_ = storage.getex(f"verify_email_code:{self._interface.chat_id}")
        if verify_code_ is None:
            email = storage.get(f"email:{self._interface.chat_id}")
            storage.setex(f"verify_email_code:{self._interface.chat_id}", VERIFY_CODE_EXPIRATION, await Mailing.verify_email(email))
            await self._interface.update_feedback(f"Verify code expired. New code sended on email: {email}", type_="info")
            await self.open()
        elif verify_code != verify_code_:
            await self._interface.update_feedback(f'Wrong verify code', type_="error")
            await self.open()
        else:
            await self._interface.basic_manager.options.update_email()


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

    async def __call__(self, hour: int):
        storage.set(f"hour:{self._interface.chat_id}", hour)
        await self._interface.basic_manager.change_notification_minute.open()


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

    async def __call__(self, minute: int):
        storage.set(f"minute:{self._interface.chat_id}", minute)
        await self._interface.basic_manager.options.update_notifications_time()


class AuthenticationWithPassword(TextMarkup):
    def __init__(self):
        super().__init__(
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
                    },
                    {
                        "back": ButtonWidget(
                            text=f"{Emoji.BACK} Back",
                            callback_data="title_screen"
                        )
                    }
                ]
            ),
            state=States.sign_in_with_password
        )

    async def open(self):
        response = await self._interface.get_user()
        if response is not None:
            if (await response.json())["email"]:
                self.markup_map['reset_password'].on()
            else:
                self.markup_map['reset_password'].off()
        await super().open()

    async def __call__(self, password: str):
        async with self._interface.session.post('/users/login', json={
            'user_id': self._interface.chat_id,
            "password": password,
        }, headers={"Authorization": storage.get("service_key")}) as response:
            response = self._interface.response_middleware(response)
            if response is not None:
                if response.status == 401:
                    await self._interface.update_feedback('Wrong password', type_="error")
                    await self.open()
                else:
                    self._interface.token = await response.text()

    async def reset_password(self):
        await self._interface.temp_message()
        response = self._interface.get_user()
        if response is not None:
            verify_code = await Mailing.verify_email((await response.json())["email"])
            storage.setex(f"verify_email_code:{self._interface.chat_id}", VERIFY_CODE_EXPIRATION, verify_code)
            await self._interface.update_feedback('Verify code sent on your email', type_="info")
            await self._interface.basic_manager.input_verify_code_reset_password.open()


class InputVerifyCodeResetPassword(TextMarkup):
    def __init__(self, interface):
        super().__init__(
            interface,
            text_map=TextMap(
                {
                    "action": TextWidget(
                        text=f'{Emoji.LOCK_AND_KEY} Enter verify code'
                    )
                }
            ),
            markup_map=MarkupMap(
                [
                    {
                        "back": ButtonWidget(text=f'{Emoji.BACK} Back', callback_data="title_screen")
                    }
                ]
            ),
            state=States.input_verify_code_reset_password
        )

    async def __call__(self, verify_code):
        await self._interface.temp_message()
        verify_code_ = storage.getex(f"verify_email_code:{self._interface.chat_id}")
        if verify_code_ is None:
            async with self._interface.session.get(
                    f'/get_user_email/{await self._interface.encoded_chat_id()}') as response:
                if response.status == 200:
                    verify_code = await Mailing.verify_email(await response.text())
                    storage.setex(f"verify_email_code:{self._interface.chat_id}", VERIFY_CODE_EXPIRATION, verify_code)
                    self._interface.update_feedback("Verify code expired. New code sent on your email.", type_="info")
                    await self.open()
                else:
                    await self._interface.handling_unexpected_error()
        elif verify_code != verify_code_:
            self._interface.update_feedback("Wrong verify code", type_="info")
            await self.open()
        else:
            await self._interface.basic_manager.input_password.open()

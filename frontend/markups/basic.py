import re

from aiogram.filters.callback_data import CallbackData
from passlib.handlers.pbkdf2 import pbkdf2_sha256
from zxcvbn import zxcvbn


from frontend.bot.FSM import States
from frontend.markups.core import TextMarkup, TextMap, TextWidget, MarkupMap, ButtonWidget, DataTextWidget

from frontend.utils import Emoji, config, encode_jwt, storage
from frontend.utils.mailing import Mailing

MAX_EMAIL_LENGTH = config.getint('limitations', 'MAX_EMAIL_LENGTH')
MAX_NAME_LENGTH = config.getint('limitations', 'MAX_NAME_LENGTH')
MAX_DESCRIPTION_LENGTH = config.getint('limitations', 'MAX_DESCRIPTION_LENGTH')
MAX_PASSWORD_LENGTH = config.getint('limitations', "MAX_PASSWORD_LENGTH")
MIN_BORDER_RANGE = config.getint('limitations', "MIN_BORDER_RANGE")
MAX_BORDER_RANGE = config.getint('limitations', "MAX_BORDER_RANGE")
STANDARD_BORDER_RANGE = config.getint('limitations', "STANDARD_BORDER_RANGE")
VERIFY_CODE_EXPIRATION = config.getint("limitations", "VERIFY_CODE_EXPIRATION")


class BasicManager:
    def __init__(self, interface):
        self._interface = interface
        self.title_screen = TitleScreen(interface)
        self.authorization_with_password = AuthorizationWithPassword(interface)

        self.profile = Profile(interface)
        self.options = Options(interface)
        self.input_password = InputPassword(interface)
        self.repeat_password = RepeatPassword(interface)
        self.resume_password = PasswordResume(interface)
        self.input_email = InputEmail(interface)
        self.input_verify_email_code = InputVerifyEmailCode(interface)
        self.input_verify_code_reset_password = InputVerifyCodeResetPassword(interface)
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

    async def authorization(self):
        async with self._interface.session.post('/sign_in', json={'telegram_id': self._interface.chat_id}) as response:
            if response.status == 401:
                await self._interface.basic_manager.authorization_with_password.open()
            elif response.status == 200:
                self._interface.token = await response.text()
                await self._interface.basic_manager.profile.open()
            else:
                await self._interface.handling_unexpected_error(response)

    async def invert_notifications(self):
        token = await encode_jwt({"telegram_id": self._interface.chat_id})
        async with self._interface.session.patch(f'/invert_notifications/{token}') as response:
            if response.status == 200:
                response = await response.text()
                if response == '1':
                    self.markup_map["notifications"].mark = Emoji.BELL
                    async with self._interface.session.get(f"/is_all_done/{await self._interface.encoded_chat_id()}") as response_:
                        if await response_.text() == "0":
                            await self._interface.notification_on()
                        else:
                            await self._interface.notification_off()
                    await self.open()
                else:
                    await self._interface.notification_off()
                    self.markup_map["notifications"].mark = Emoji.NOT_BELL
                    await self.open()
            elif response.status == 401:
                await self._interface.close_session()
            else:
                await self._interface.handling_unexpected_error(response)


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
        self.text_map['hello'].data = self._interface.first_name
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
        async with self._interface.session.get(f'/notification_time/{await self._interface.encoded_chat_id()}') as response:
            if response.status == 200:
                time_ = await response.json()
                minute = str(time_['minute'])
                minute = "0" + minute if len(minute) < 2 else minute
                self.text_map["notification_time"].data = f"{time_['hour']}:{minute}"
            else:
                await self._interface.handling_unexpected_error(response)
                return

        async with self._interface.session.get(f"/is_password_set/{await self._interface.encoded_chat_id()}") as response:
            if response.status == 200:
                response = await response.text()
                if response == '1':
                    self.markup_map['delete_password'].on()
                    self.markup_map['input_password'].text = f'{Emoji.KEY + Emoji.UP} Change password'
                else:
                    self.markup_map['delete_password'].off()
                    self.markup_map["input_password"].text = f"{Emoji.KEY + Emoji.PLUS} Add password"
            else:
                await self._interface.handling_unexpected_error(response)
                return

        async with self._interface.session.get(f"/is_email_set/{await self._interface.encoded_chat_id()}") as response:
            if response.status == 200:
                response = await response.text()
                if response == '1':
                    self.markup_map['delete_email'].on()
                    self.markup_map['input_email'].text = f'{Emoji.ENVELOPE + Emoji.UP} Change email'
                else:
                    self.markup_map['delete_email'].off()
                    self.markup_map["input_email"].text = f"{Emoji.ENVELOPE + Emoji.PLUS} Add email"
            else:
                await self._interface.handling_unexpected_error(response)
                return

        await super().open()

    async def update_password(self):
        payload = {
            "telegram_id": self._interface.chat_id,
            "hash": storage.get(f"hash:{self._interface.chat_id}"),
        }
        async with (self._interface.session.patch(f"/update_password/{await encode_jwt(payload)}") as response):
            if response.status == 200:
                await self._interface.update_feedback(f'Password updated', type_="info")
                await self._interface.basic_manager.title_screen.open()
            elif response.status == 401:
                await self._interface.close_session()
            else:
                await self._interface.handling_unexpected_error(response)

    async def delete_password(self):
        async with self._interface.session.delete("/delete_password") as response:
            if response.status == 200:
                self.markup_map["delete_password"].off()
                await self._interface.update_feedback("password deleted")
                await self.open()
            elif response.status == 401:
                await self._interface.close_session()
            else:
                await self._interface.handling_unexpected_error(response)

    async def update_email(self):
        async with (self._interface.session.patch('/update_email', json={
            "email": storage.get(f"email:{self._interface.chat_id}"),
        }) as response):
            if response.status == 200:
                await self._interface.update_feedback(f'Email updated', type_="info")
                await self.open()
            elif response.status == 401:
                await self._interface.close_session()
            else:
                await self._interface.handling_unexpected_error(response)

    async def delete_email(self):
        async with self._interface.session.delete("/delete_email") as response:
            if response.status == 200:
                self.markup_map["delete_email"].off()
                await self._interface.update_feedback("password deleted")
                await self.open()
            elif response.status == 401:
                await self._interface.close_session()
            else:
                await self._interface.handling_unexpected_error(response)

    async def update_notifications_time(self):
        hour = storage.get(f"hour:{self._interface.chat_id}")
        minute = storage.get(f"minute:{self._interface.chat_id}")

        async with self._interface.session.patch('/notification_time', json={"hour": hour, "minute": minute}) as response:
            if response.status == 200:
                self.text_map["notification_time"].data = f"{hour}:{minute}"
                await self.open()
            elif response.status == 401:
                await self._interface.close_session()
            else:
                await self._interface.handling_unexpected_error(response)

        async with self._interface.session.get(f"/is_all_done/{await self._interface.encoded_chat_id()}") as response:
            if response.status == 200:
                if await response.text() == "1":
                    await self._interface.notification_off()
                else:
                    await self._interface.notification_on()
            elif response.status == 401:
                await self._interface.close_session()
            else:
                await self._interface.handling_unexpected_error(response)


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
        await self.text_map['warning'].reset()
        self.text_map['warning'].off()
        await self.text_map['suggestions'].reset()
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
        elif not re.fullmatch(r'\w+@\w+\.\w+', email, flags=re.I):
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
        async with self._interface.session.get(f"/is_email_set/{await self._interface.encoded_chat_id()}") as response:
            if response.status == 200:
                response = await response.text()
                if response == '1':
                    self.markup_map['reset_password'].on()
                else:
                    self.markup_map['reset_password'].off()
            else:
                await self._interface.handling_unexpected_error(response)

        await super().open()

    async def __call__(self, password: str):
        async with self._interface.session.post('/sign_in', json={
            'telegram_id': self._interface.chat_id, "password": password
        }) as response:
            if response.status == 200:
                self._interface.token = await response.text()
                await self._interface.basic_manager.profile.open()
            elif response.status == 401:
                await self._interface.update_feedback('Wrong password', type_="error")
                await self.open()
            else:
                await self._interface.handling_unexpected_error(response)

    async def reset_password(self):
        await self._interface.temp_message()
        async with self._interface.session.get(f'/get_user_email/{await self._interface.encoded_chat_id()}') as response:
            if response.status == 200:
                verify_code = await Mailing.verify_email(await response.text())
                storage.setex(f"verify_email_code:{self._interface.chat_id}", VERIFY_CODE_EXPIRATION, verify_code)
                await self._interface.update_feedback('Verify code sent on your email', type_="info")
                await self._interface.basic_manager.input_verify_code_reset_password.open()
            else:
                await self._interface.handling_unexpected_error(response)


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

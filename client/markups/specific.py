import time
from datetime import datetime

from aiogram.filters.callback_data import CallbackData
from zxcvbn import zxcvbn

from client.bot.FSM import States
from client.markups import InitializeMarkupInterface, Back, Conform, Input
from client.markups.core import TextWidget, ButtonWidget, DataTextWidget, InitializeApiMarkupInterface
from client.utils import Emoji


class TitleScreen(InitializeApiMarkupInterface):
    def __init__(self, user_id: str):
        self._user_id = user_id
        super().__init__()

    async def init(self):
        info = TextWidget(text=f"{Emoji.BRAIN} Psychological service")
        sign_in = ButtonWidget(text=f'{Emoji.DOOR} Sign in', callback_data='authorization')
        self.text_message_markup.add_text_row(info)
        self.text_message_markup.add_button_in_new_row(sign_in)
        self.text_message_markup.add_button_in_new_row(await self._init_notification(self._user_id))
        return self.text_message_markup

    async def _init_notification(self, user_id: str):
        notifications_button = ButtonWidget(
            text="Notifications",
            callback_data="invert_notifications",
        )
        data, code = await self._api.get_user(user_id)
        if code == 200:
            if data["notifications"]:
                notifications_button.mark = Emoji.BELL
            else:
                notifications_button.mark = Emoji.NOT_BELL
        else:
            notifications_button.text = Emoji.DENIAL + " Error"
            notifications_button.mark = Emoji.RED_QUESTION
        return notifications_button


class AuthenticationWithPassword(InitializeApiMarkupInterface):
    def __init__(self, user_id: str, text=f'{Emoji.KEY} Enter the password'):
        self._user_id = user_id
        self._input = Input(text)
        super().__init__(States.input_text_sign_in_with_password)

    async def init(self):
        button = await self._init_reset_password(self._user_id)
        if button is not None:
            self.text_message_markup.add_buttons_in_new_row(button)
            self.text_message_markup.attach(self._input)
        else:
            self.text_message_markup.attach(self._input)

        return self

    async def _init_reset_password(self, user_id: str):
        reset_password = ButtonWidget(
            text=f'{Emoji.CYCLE} Reset password',
            callback_data='reset_password'
        )
        data, code = await self._api.get_user(user_id)
        if code == 200 and data["email"]:
            return reset_password


class PasswordResume(InitializeMarkupInterface):
    _strength_marks = {
        4: f'{Emoji.GREEN_CIRCLE} Reliable',
        3: f'{Emoji.YELLOW_CIRCLE} Good',
        2: f'{Emoji.ORANGE_CIRCLE} Medium',
        1: f'{Emoji.RED_CIRCLE} Bad',
        0: f'{Emoji.WARNING}️ Worst'
    }

    def __init__(self, password: str):
        super().__init__()
        self.text_message_markup = Conform(
            info=self._init_password_resume(password),
            yes_text="Conform",
            no_text="Cancel",
            yes_callback_data="update_password",
            no_callback_data="input_password"
        ).text_message_markup

    @classmethod
    def _init_password_resume(cls, password: str):
        grade = zxcvbn(password)
        grade_text = f'{Emoji.DIAGRAM} Password grade\n'
        grade_text += f"{Emoji.SHIELD} Strength: " + cls._strength_marks[grade['score']] + '\n'

        warning = grade['feedback']['warning']
        if warning:
            grade_text += f"{Emoji.WARNING} Warning: " + warning

        suggestions = grade['feedback']['suggestions']
        if suggestions:
            suggestions_ = f'{Emoji.SHINE_STAR} Suggestions:\n'
            for n, suggestion in enumerate(suggestions, start=1):
                suggestions_ += f'{n}) {suggestion}'
            grade_text += suggestions_
        return grade_text


class Profile(InitializeMarkupInterface):
    def __init__(self, name: str):
        super().__init__()
        self.text_message_markup.add_text_row(TextWidget(text=f"Hello, {name}"))
        self.text_message_markup.keyboard_map = [
            [
                ButtonWidget(text=f"{Emoji.DIAGRAM} Targets", callback_data="targets_control"),
            ],
            [
                ButtonWidget(text=f'{Emoji.GEAR} Options', callback_data="options"),
            ],
            [
                ButtonWidget(text=f'{Emoji.BACK} Exit', callback_data="title_screen"),
            ],
        ]


class Options(InitializeApiMarkupInterface):
    def __init__(self, user_id: str):
        super().__init__()
        self._user_id = user_id
        self.local_time = DataTextWidget(text=f"{Emoji.WATCH} Server time", data=f"{datetime.now().strftime('%d.%m.%y %H:%M')} UTC{time.tzname[0]}")
        self.time = DataTextWidget(text=f"{Emoji.BELL} Notification time")
        self.delete_password = ButtonWidget(text=f"{Emoji.KEY + Emoji.DENIAL} Delete password", callback_data="delete_password")
        self.input_password = ButtonWidget(callback_data="input_password")
        self.delete_email = ButtonWidget(text=f"{Emoji.EMAIL + Emoji.DENIAL} Delete email", callback_data="delete_email")
        self.input_email = ButtonWidget(callback_data="input_email")
        self.change_notifications = ButtonWidget(
            text=f"{Emoji.BELL} Change notification time",
            callback_data="change_notification_time"
        )

    async def init(self):
        data, code = await self._api.get_user(self._user_id)
        if code == 200:
            time_ = data["notification_time"]
            self.time.data = f"{time_['hour']}:{str(time_['minute']).zfill(2)}"
            self.text_message_markup.add_texts_rows(self.local_time, self.time)
            if data["hash"]:
                self.input_password.text = f'{Emoji.KEY} Change password'
                self.text_message_markup.add_buttons_in_new_row(self.input_password, self.delete_password)
            else:
                self.input_password.text = f"{Emoji.KEY} Add password"
                self.text_message_markup.add_button_in_new_row(self.input_password)

            if data["email"]:
                self.input_email.text = f'{Emoji.EMAIL} Change email'
                self.text_message_markup.add_buttons_in_new_row(self.input_email, self.delete_email)
            else:
                self.input_email.text = f"{Emoji.EMAIL} Add email"
                self.text_message_markup.add_button_in_new_row(self.input_email)
        else:
            self.text_message_markup.add_text_row(TextWidget(text=f"{Emoji.DENIAL} Internal server error"))

        self.text_message_markup.add_button_in_new_row(self.change_notifications)
        self.text_message_markup.attach(Back(callback_data="profile"))
        return self


class NotificationsHourCallbackData(CallbackData, prefix="notification_hour"):
    hour: int


class ChangeNotificationsHour(InitializeMarkupInterface):
    def __init__(self):
        super().__init__()
        self._info = TextWidget(text=f"{Emoji.CLOCK} Choose notification hour")
        self._hours = (
            ButtonWidget(text=str(hour), callback_data=NotificationsHourCallbackData(hour=hour))
            for hour in range(24)
        )
        self.text_message_markup.add_text_row(self._info)
        self.text_message_markup.add_buttons_in_last_row(*self._hours)
        self.text_message_markup.attach(Back(text=F"{Emoji.DENIAL} Cancel"))


class NotificationsMinuteCallbackData(CallbackData, prefix="notification_minute"):
    minute: int


class ChangeNotificationsMinute(InitializeMarkupInterface):
    def __init__(self):
        super().__init__()
        self._info = TextWidget(text=f"{Emoji.CLOCK} Choose notification minute")
        self._minutes = (
            ButtonWidget(text=str(minute), callback_data=NotificationsMinuteCallbackData(minute=minute))
            for minute in range(60)
        )
        self.text_message_markup.add_text_row(self._info)
        self.text_message_markup.add_buttons_in_last_row(*self._minutes)
        self.text_message_markup.attach(Back(text=F"{Emoji.DENIAL} Cancel"))

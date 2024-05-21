

from aiogram.filters.callback_data import CallbackData
from passlib.handlers.pbkdf2 import pbkdf2_sha256
from zxcvbn import zxcvbn

from client.api import Api
from client.bot.FSM import States
from client.markups import InitializeMarkupInterface, Back, Conform, Info
from client.markups.core import TextMarkup, TextWidget, KeyboardMarkup, ButtonWidget, DataTextWidget, TextMessageMarkup, \
    InitializeApiMarkupInterface
from client.utils import Emoji, config
from client.utils.mailing import Mailing


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
    def __init__(self, user_id: str):
        self._user_id = user_id
        super().__init__(States.input_text_sign_in_with_password)

    async def init(self):
        info = TextWidget(text=f'{Emoji.KEY} Enter the password')
        self.text_message_markup.add_text_row(info)
        button = await self._init_reset_password(self._user_id)
        if button is not None:
            self.text_message_markup.add_button_in_new_row(button)
        self.text_message_markup.attach(Back())
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
        self.time = DataTextWidget(text=f"{Emoji.BELL + Emoji.CLOCK} Notification time")
        self.delete_password = ButtonWidget(text=f"{Emoji.KEY + Emoji.DENIAL} Delete password", callback_data="delete_password")
        self.input_password = ButtonWidget(callback_data="input_password")
        self.delete_email = ButtonWidget(text=f"{Emoji.ENVELOPE + Emoji.DENIAL} Delete email", callback_data="delete_email")
        self.input_email = ButtonWidget(callback_data="input_email")
        self.change_notifications = ButtonWidget(
            text=f"{Emoji.BELL + Emoji.CLOCK} Change notification time",
            callback_data="change_notification_time"
        )

    async def init(self):
        data, code = await self._api.get_user(self._user_id)
        if code == 200:
            time_ = data["notification_time"]
            self.time.data = f"{time_['hour']}:{str(time_['minute']).zfill(2)}"
            self.text_message_markup.add_text_row(self.time)
            if data["hash"]:
                self.input_password.text = f'{Emoji.KEY + Emoji.UP} Change password'
                self.text_message_markup.add_buttons_in_new_row(self.input_password, self.delete_password)
            else:
                self.input_password.text = f"{Emoji.KEY + Emoji.PLUS} Add password"
                self.text_message_markup.add_button_in_new_row(self.input_password)

            if data["email"]:
                self.input_email.text = f'{Emoji.ENVELOPE + Emoji.UP} Change email'
                self.text_message_markup.add_buttons_in_new_row(self.input_email, self.delete_email)
            else:
                self.input_email.text = f"{Emoji.ENVELOPE + Emoji.PLUS} Add email"
                self.text_message_markup.add_button_in_new_row(self.input_email)
        else:
            self.text_message_markup.add_text_row(TextWidget(text=f"{Emoji.DENIAL} Internal server error"))

        self.text_message_markup.add_button_in_new_row(self.change_notifications)
        self.text_message_markup.attach(Back(callback_data="profile"))
        return self


# class InputVerifyEmailCode(TextMarkup):
#     def __init__(self, interface):
#         super().__init__(
#             interface,
#             text_map=TextMap(
#                 {
#                     "action": TextWidget(
#                         text=f'{Emoji.LOCK_AND_KEY} Enter verify code'
#                     )
#                 }
#             ),
#             markup_map=MarkupMap(
#                 [
#                     {
#                         "back": ButtonWidget(text=f'{Emoji.CYCLE} Change email', callback_data="create_email")
#                     }
#                 ]
#             ),
#             state=States.input_verify_email_code
#         )
#
#     async def __call__(self, verify_code):
#         await self._interface.temp_message()
#         verify_code_ = storage.getex(f"verify_email_code:{self._interface._user_id}")
#         if verify_code_ is None:
#             email = storage.get(f"email:{self._interface._user_id}")
#             storage.setex(f"verify_email_code:{self._interface._user_id}", VERIFY_CODE_EXPIRATION, await Mailing.verify_email(email))
#             await self._interface.update_feedback(f"Verify code expired. New code sended on email: {email}", type_="info")
#             await self.open()
#         elif verify_code != verify_code_:
#             await self._interface.update_feedback(f'Wrong verify code', type_="error")
#             await self.open()
#         else:
#             await self._interface.basic_manager.options.update_email()
#
#
# class NotificationHourCallbackData(CallbackData, prefix="notification_hour"):
#     hour: int
#
#
# class ChangeNotificationsHour(TextMarkup):
#     def __init__(self, interface):
#         super().__init__(
#             interface,
#             TextMap(
#                 {
#                     "info": TextWidget(f"{Emoji.CLOCK} Choose notification hour")
#                 }
#             ),
#             MarkupMap(
#                 [
#                     {
#                         str(hour): ButtonWidget(
#                             text=str(hour),
#                             callback_data=NotificationHourCallbackData(hour=hour)
#                         ) for hour in range(start, start + 8)
#                     }
#                     for start in range(0, 24, 8)
#                 ] + [
#                     {
#                         "back": ButtonWidget(text=f"{Emoji.BACK} Cancel", callback_data='options')
#                     }
#                 ]
#             )
#         )
#
#     async def __call__(self, hour: int):
#         storage.set(f"hour:{self._interface._user_id}", hour)
#         await self._interface.basic_manager.change_notification_minute.open()
#
#
# class NotificationMinuteCallbackData(CallbackData, prefix="notification_minute"):
#     minute: int
#
#
# class ChangeNotificationsMinute(TextMarkup):
#     def __init__(self, interface):
#         super().__init__(
#             interface,
#             TextMap(
#                 {
#                     "info": TextWidget(f"{Emoji.CLOCK} Choose notification minute")
#                 }
#             ),
#             MarkupMap(
#                 [
#                     {
#                         str(minute): ButtonWidget(
#                             text=str(minute),
#                             callback_data=NotificationMinuteCallbackData(minute=minute)
#                         ) for minute in range(start, start + 8)
#                     }
#                     for start in range(0, 56, 8)
#                 ] + [
#                     {
#                         str(minute): ButtonWidget(
#                             text=str(minute),
#                             callback_data=NotificationMinuteCallbackData(minute=minute)
#                         ) for minute in range(56, 60)
#                     }
#                 ] + [
#                     {
#                         "back": ButtonWidget(text=f"{Emoji.BACK} Cancel", callback_data='options')
#                     }
#                 ]
#             )
#         )
#
#     async def __call__(self, minute: int):
#         storage.set(f"minute:{self._interface._user_id}", minute)
#         await self._interface.basic_manager.options.update_notifications_time()
#
#
# class FeedbackMixin:
#     _feedback_headers = {
#         "default": DataTextWidget(header=f'{Emoji.REPORT} Feedback'),
#         "info": DataTextWidget(header=f"{Emoji.INFO} Info"),
#         "error": DataTextWidget(header=f"{Emoji.DENIAL} Error"),
#     }
#
#

#
#
# class InputVerifyCodeResetPassword(TextMarkup):
#     def __init__(self, interface):
#         super().__init__(
#             interface,
#             text_map=TextMap(
#                 {
#                     "action": TextWidget(
#                         text=f'{Emoji.LOCK_AND_KEY} Enter verify code'
#                     )
#                 }
#             ),
#             markup_map=MarkupMap(
#                 [
#                     {
#                         "back": ButtonWidget(text=f'{Emoji.BACK} Back', callback_data="title_screen")
#                     }
#                 ]
#             ),
#             state=States.input_verify_code_reset_password
#         )
#
#     async def __call__(self, verify_code):
#         await self._interface.temp_message()
#         verify_code_ = storage.getex(f"verify_email_code:{self._interface._user_id}")
#         if verify_code_ is None:
#             async with self._interface.session.get(
#                     f'/get_user_email/{await self._interface.encoded_chat_id()}') as response:
#                 if response.status == 200:
#                     verify_code = await Mailing.verify_email(await response.text())
#                     storage.setex(f"verify_email_code:{self._interface._user_id}", VERIFY_CODE_EXPIRATION, verify_code)
#                     self._interface.update_feedback("Verify code expired. New code sent on your email.", type_="info")
#                     await self.open()
#                 else:
#                     await self._interface.handling_unexpected_error()
#         elif verify_code != verify_code_:
#             self._interface.update_feedback("Wrong verify code", type_="info")
#             await self.open()
#         else:
#             await self._interface.basic_manager.input_password.open()

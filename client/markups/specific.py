import time
from datetime import datetime

from aiogram.filters.callback_data import CallbackData
from zxcvbn import zxcvbn

from client.bot.FSM import States
from client.markups import InitializeMarkupInterface, Back, Conform, Input, Info, ErrorInfo, \
    LeftBackRight
from client.markups.core import TextWidget, ButtonWidget, DataTextWidget, AsyncInitializeMarkupInterface
from client.utils import Emoji, create_progress_text, config


class TitleScreen(AsyncInitializeMarkupInterface):
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


class AuthenticationWithPassword(AsyncInitializeMarkupInterface):
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


MINUTE_INCREASE_PROGRESS = config.get("limitations", "MINUTE_INCREASE_PROGRESS")
HOUR_INCREASE_PROGRESS = config.get("limitations", "HOUR_INCREASE_PROGRESS")


class Options(AsyncInitializeMarkupInterface):
    def __init__(self, user_id: str):
        super().__init__()
        self._user_id = user_id

    async def init(self):
        info = TextWidget(text=f"{Emoji.INFO} Progress for each target will be increased at"
                               f" {HOUR_INCREASE_PROGRESS.zfill(2)}:{MINUTE_INCREASE_PROGRESS.zfill(2)} of each day")
        local_time = DataTextWidget(
            text=f"{Emoji.WATCH} Server time",
            data=f"{datetime.now().strftime('%d.%m.%y %H:%M')} UTC{time.tzname[0]}"
        )
        time_ = DataTextWidget(text=f"{Emoji.BELL} Notification time")
        delete_password = ButtonWidget(text=f"{Emoji.KEY + Emoji.DENIAL} Delete password",
                                       callback_data="delete_password")
        input_password = ButtonWidget(callback_data="input_password")
        delete_email = ButtonWidget(text=f"{Emoji.EMAIL + Emoji.DENIAL} Delete email",
                                    callback_data="delete_email")
        input_email = ButtonWidget(callback_data="input_email")
        change_notifications = ButtonWidget(
            text=f"{Emoji.BELL} Change notification time",
            callback_data="change_notification_time"
        )
        data, code = await self._api.get_user(self._user_id)
        if code == 200:
            notifications_time_ = data["notification_time"]
            time_.data = f"{notifications_time_['hour']}:{str(notifications_time_['minute']).zfill(2)}"
            self.text_message_markup.add_texts_rows(info, local_time, time_)
            if data["hash"]:
                input_password.text = f'{Emoji.KEY} Change password'
                self.text_message_markup.add_buttons_in_new_row(input_password, delete_password)
            else:
                input_password.text = f"{Emoji.KEY} Add password"
                self.text_message_markup.add_button_in_new_row(input_password)

            if data["email"]:
                input_email.text = f'{Emoji.EMAIL} Change email'
                self.text_message_markup.add_buttons_in_new_row(input_email, delete_email)
            else:
                input_email.text = f"{Emoji.EMAIL} Add email"
                self.text_message_markup.add_button_in_new_row(input_email)
        else:
            self.text_message_markup.add_text_row(TextWidget(text=f"{Emoji.DENIAL} Internal server error"))

        self.text_message_markup.add_button_in_new_row(change_notifications)
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


class TargetsControl(AsyncInitializeMarkupInterface):
    def __init__(self, token: str):
        super().__init__()
        self._token = token

    async def init(self):
        targets, code = await self._api.get_targets(self._token)
        if code == 200:
            if targets:
                total_current_targets_completed = sum(
                    (1 for target in targets if target["completed"] and target["progress"] != target["border_progress"])
                )
                total_targets_uncompleted = sum(
                    (1 for target in targets if target["progress"] != target["border_progress"])
                )
                progress = create_progress_text(
                    total_current_targets_completed,
                    total_targets_uncompleted,
                )
                progress = TextWidget(text=f"Progress today: {progress}")
                self.text_message_markup.add_text_row(progress)
            else:
                progress = TextWidget(text=f"No targets so far {Emoji.CRYING_CAT}")
                self.text_message_markup.add_text_row(progress)
        else:
            progress = TextWidget(text=f"{Emoji.DENIAL} Error")
            self.text_message_markup.add_text_row(progress)

        self.text_message_markup.keyboard_map = [
            [
                ButtonWidget(text=f"{Emoji.DIAGRAM} Current targets", callback_data="current_targets"),
            ],
            [
                ButtonWidget(text=f"{Emoji.SPROUT} Create target", callback_data="create_target"),
            ],
            [
                ButtonWidget(text=f"{Emoji.TROPHY} Achievements", callback_data="manage_targets"),
            ],
            [
                ButtonWidget(text=f"{Emoji.BACK} Back", callback_data="profile")
            ]
        ]
        return self


class CurrentTargetsListLeftCallbackData(CallbackData, prefix="left_current_targets_list"):
    page: int


class CurrentTargetCallbackData(CallbackData, prefix='current_target'):
    id: int


class CurrentTargetsListRightCallbackData(CallbackData, prefix="right_current_targets_list"):
    page: int


class CurrentTargetsList(AsyncInitializeMarkupInterface):
    _targets_per_page = 10

    def __init__(self, token: str, page: int = 0):
        super().__init__()
        self._page = page
        self._token = token

    async def init(self):
        data, code = await self._api.get_targets(self._token)
        if code == 200:
            if not data:
                self.text_message_markup.attach(Info(
                    f"No targets so far {Emoji.CRYING_CAT}",
                    callback_data="targets_control"
                ))
            else:
                targets = [target for target in data if target["progress"] != target["border_progress"]]
                count = 0
                completed_targets_today = 0
                pages = []
                page = []
                for target in targets:
                    button = ButtonWidget(text=target["name"], callback_data=CurrentTargetCallbackData(id=target["id"]))
                    if target["completed"]:
                        completed_targets_today += 1
                        button.mark = Emoji.OK
                    if count == self._targets_per_page:
                        count = 0
                        pages.append(page)
                        page = []
                    page.append(button)
                    count += 1
                pages.append(page)

                # progress = create_progress_text(
                #     completed_targets_today,
                #     len(targets),
                # )
                self.text_message_markup.add_text_row(TextWidget(text=f"{Emoji.SPROUT} Current targets: "))
                for button in pages[self._page]:
                    self.text_message_markup.add_button_in_new_row(button)

                total_pages = len(pages)

                if len(targets) > self._targets_per_page:
                    self.text_message_markup.attach(LeftBackRight(
                        left_callback_data=CurrentTargetsListLeftCallbackData(page=(self._page - 1) % total_pages),
                        right_callback_data=CurrentTargetsListRightCallbackData(page=(self._page + 1) % total_pages),
                        back_callback_data="profile"

                    ))
                else:
                    self.text_message_markup.attach(Back(callback_data="targets_control"))
        else:
            self.text_message_markup.attach(ErrorInfo())
        return self


class Target(AsyncInitializeMarkupInterface):
    def __init__(self, token: str, id_: int):
        super().__init__()
        self._token = token
        self._id = id_

    async def init(self):
        data, code = await self._api.get_target(self._token, self._id)
        if code == 200:
            text_map = [
                TextWidget(text=f"{Emoji.SPROUT} {data['name']}"),
                DataTextWidget(text=f"{Emoji.LIST_WITH_PENCIL} Description", data=data["description"]),
            ]
            progress = TextWidget(text=create_progress_text(data["progress"], data["border_progress"],
                                                            show_digits=False) + f"{data['progress']}/{data['border_progress']}")
            done = TextWidget(text=Emoji.OK)
            keyboard_map = [
                [
                    ButtonWidget(
                        text=f"Mark as undone {Emoji.DENIAL}" if data["completed"] else f"Mark as done {Emoji.OK}",
                        callback_data="invert_completed"
                    )
                ],
                [
                    ButtonWidget(text=f"Change name {Emoji.SPROUT}", callback_data="change_name"),
                    ButtonWidget(text=f"Change description {Emoji.LIST_WITH_PENCIL}",
                                 callback_data="change_description"),
                ],
                [
                    ButtonWidget(text=f"Delete target {Emoji.DENIAL}", callback_data="delete_target")
                ],
            ]
            back = Back()

            self.text_message_markup.text_map = text_map
            self.text_message_markup.add_text_row(progress)
            if data["completed"]:
                self.text_message_markup.add_text_row(done)
            self.text_message_markup.keyboard_map = keyboard_map
            self.text_message_markup.attach(back)
        else:
            self.text_message_markup.attach(ErrorInfo())
        return self


class InputBorder(InitializeMarkupInterface):
    def __init__(self):
        super().__init__(States.input_text_target_border)
        text = TextWidget(text=f"How many days do you want to set for border progress? {Emoji.FLAG_FINISH}\n"
                               "(By default border is 21 days. This is standard value for habit fix)")
        skip = ButtonWidget(text=f"{Emoji.SKIP} Skip", callback_data="conform_create_target")
        back = Back(text=f"{Emoji.DENIAL} Cancel")

        self.text_message_markup.add_text_row(text)
        self.text_message_markup.add_button_in_new_row(skip)
        self.text_message_markup.attach(back)

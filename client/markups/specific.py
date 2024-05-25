import time
from datetime import datetime

from aiogram.filters.callback_data import CallbackData
from zxcvbn import zxcvbn

from client.bot.FSM import States
from client.markups import (
    InitializeMarkupInterface,
    Back,
    Conform,
    Info,
    ErrorInfo,
    LeftBackRight,
)
from client.markups.core import (
    TextWidget,
    ButtonWidget,
    DataTextWidget,
    AsyncInitializeMarkupInterface,
)
from client.utils import Emoji, create_progress_text, config


class TitleScreen(AsyncInitializeMarkupInterface):
    def __init__(self, user_id: str):
        self._user_id = user_id
        super().__init__()

    async def init(self):
        info = TextWidget(text=f"{Emoji.BRAIN} Psychological service")
        sign_in = ButtonWidget(
            text=f"{Emoji.DOOR} Sign in", callback_data="authorization"
        )
        notifications = await self._init_notifications(self._user_id)

        self.text_message_markup.add_text_row(info)
        self.text_message_markup.add_button_in_new_row(sign_in)
        self.text_message_markup.add_button_in_new_row(notifications)
        return self

    async def _init_notifications(self, user_id: str):
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
    def __init__(
        self,
        user_id: str,
        text: str = f"{Emoji.KEY} Enter the password",
        back_callback_data: str | CallbackData = "return_to_context",
    ):
        self._user_id = user_id
        self.text = text
        self.back_callback_data = back_callback_data
        super().__init__(States.input_text_sign_in_with_password)

    async def init(self):
        info = TextWidget(text=self.text)
        reset_password = ButtonWidget(
            text=f"{Emoji.CYCLE} Reset password", callback_data="reset_password"
        )
        back = Back(callback_data=self.back_callback_data)

        self.text_message_markup.add_text_row(info)
        data, code = await self._api.get_user(self._user_id)
        if code == 200 and data["email"]:
            self.text_message_markup.add_button_in_new_row(reset_password)
        self.text_message_markup.attach(back)
        return self


class PasswordResume(InitializeMarkupInterface):
    _strength_marks = {
        4: f"{Emoji.GREEN_CIRCLE} Reliable",
        3: f"{Emoji.YELLOW_CIRCLE} Good",
        2: f"{Emoji.ORANGE_CIRCLE} Medium",
        1: f"{Emoji.RED_CIRCLE} Bad",
        0: f"{Emoji.WARNING}️ Worst",
    }

    def __init__(
        self,
        password: str,
        *,
        yes_text: str = f"{Emoji.OK} Conform",
        no_text: str = f"{Emoji.DENIAL} Cancel",
        yes_callback_data: str | CallbackData = "update_password",
        no_callback_data: str | CallbackData = "input_password",
    ):
        super().__init__()
        conform = Conform(
            text=self._password_resume(password),
            yes_text=yes_text,
            no_text=no_text,
            yes_callback_data=yes_callback_data,
            no_callback_data=no_callback_data,
        )

        self.text_message_markup.attach(conform)

    @classmethod
    def _password_resume(cls, password: str):
        grade = zxcvbn(password)
        grade_text = f"{Emoji.DIAGRAM} Password grade\n"
        grade_text += (
            f"{Emoji.SHIELD} Strength: " + cls._strength_marks[grade["score"]] + "\n"
        )

        warning = grade["feedback"]["warning"]
        if warning:
            grade_text += f"{Emoji.WARNING} Warning: " + warning

        suggestions = grade["feedback"]["suggestions"]
        if suggestions:
            suggestions_ = f"{Emoji.SHINE_STAR} Suggestions:\n"
            for n, suggestion in enumerate(suggestions, start=1):
                suggestions_ += f"{n}) {suggestion}"
            grade_text += suggestions_
        return grade_text


class Profile(AsyncInitializeMarkupInterface):
    def __init__(
        self,
        token: str,
        name: str,
        back_callback_data: str | CallbackData = "title_screen",
    ):
        super().__init__()
        self.token = token
        self.name = name
        self.back_callback_data = back_callback_data

    async def init(self):
        hello = TextWidget(text=f"Hello, {self.name}")

        targets, code = await self._api.get_targets(self.token)
        if code == 200:
            if not targets:
                progress = TextWidget(text=f"No targets so far {Emoji.CRYING_CAT}")
            else:
                total_current_targets_completed = sum(
                    (
                        1
                        for target in targets
                        if target["completed"]
                        and target["progress"] != target["border_progress"]
                    )
                )
                total_targets_uncompleted = sum(
                    (
                        1
                        for target in targets
                        if target["progress"] != target["border_progress"]
                    )
                )
                progress = create_progress_text(
                    total_current_targets_completed,
                    total_targets_uncompleted,
                )
                progress = TextWidget(text=f"Progress today: {progress}")
        else:
            progress = TextWidget(text=f"{Emoji.DENIAL} Error")

        keyboard_map = [
            [
                ButtonWidget(
                    text=f"{Emoji.DIAGRAM} Targets", callback_data="current_targets"
                ),
            ],
            [
                ButtonWidget(
                    text=f"{Emoji.SPROUT} Create target", callback_data="create_target"
                ),
            ],
            [
                ButtonWidget(text=f"{Emoji.GEAR} Options", callback_data="options"),
            ],
            [
                ButtonWidget(
                    text=f"{Emoji.BACK} Exit", callback_data=self.back_callback_data
                ),
            ],
        ]
        self.text_message_markup.add_texts_rows(hello, progress)
        self.text_message_markup.keyboard_map = keyboard_map
        return self


MINUTE_INCREASE_PROGRESS = config.get("limitations", "MINUTE_INCREASE_PROGRESS")
HOUR_INCREASE_PROGRESS = config.get("limitations", "HOUR_INCREASE_PROGRESS")


class Options(AsyncInitializeMarkupInterface):
    def __init__(
        self, user_id: str, back_callback_data: str | CallbackData = "profile"
    ):
        super().__init__()
        self._user_id = user_id
        self._back_callback_data = back_callback_data

    async def init(self):
        info = DataTextWidget(
            text=f"{Emoji.INFO} Progress for each target every day will be increased at",
            data=f"{HOUR_INCREASE_PROGRESS.zfill(2)}:UTC+07",
            sep=" ",
        )
        local_time = DataTextWidget(
            text=f"{Emoji.WATCH} Server time",
            data=f"{datetime.now().strftime('%d.%m.%y %H:%M')} {''.join(time.tzname)}",
        )
        time_ = DataTextWidget(text=f"{Emoji.BELL} Notification time")
        delete_password = ButtonWidget(
            text=f"{Emoji.KEY + Emoji.DENIAL} Delete password",
            callback_data="delete_password",
        )
        input_password = ButtonWidget(callback_data="input_password")
        delete_email = ButtonWidget(
            text=f"{Emoji.EMAIL + Emoji.DENIAL} Delete email",
            callback_data="delete_email",
        )
        input_email = ButtonWidget(callback_data="input_email")
        change_notifications = ButtonWidget(
            text=f"{Emoji.BELL} Change notification time",
            callback_data="change_notification_time",
        )
        back = Back(callback_data=self._back_callback_data)

        data, code = await self._api.get_user(self._user_id)
        if code == 200:
            notifications_time_ = data["notification_time"]
            time_.data = f"{notifications_time_['hour']}:{str(notifications_time_['minute']).zfill(2)}"
            self.text_message_markup.add_texts_rows(info, local_time, time_)
            if data["hash"]:
                input_password.text = f"{Emoji.KEY} Change password"
                self.text_message_markup.add_buttons_in_new_row(
                    input_password, delete_password
                )
            else:
                input_password.text = f"{Emoji.KEY} Add password"
                self.text_message_markup.add_button_in_new_row(input_password)

            if data["email"]:
                input_email.text = f"{Emoji.EMAIL} Change email"
                self.text_message_markup.add_buttons_in_new_row(
                    input_email, delete_email
                )
            else:
                input_email.text = f"{Emoji.EMAIL} Add email"
                self.text_message_markup.add_button_in_new_row(input_email)

            self.text_message_markup.add_button_in_new_row(change_notifications)
            self.text_message_markup.attach(back)
        else:
            self.text_message_markup.add_text_row(ErrorInfo())
        return self


class NotificationsHourCallbackData(CallbackData, prefix="notification_hour"):
    hour: int


class ChangeNotificationsHour(InitializeMarkupInterface):
    def __init__(self, back_callback_data: str | CallbackData = "return_to_context"):
        super().__init__()
        info = TextWidget(text=f"{Emoji.CLOCK} Choose notification hour")
        hours = (
            ButtonWidget(
                text=str(hour), callback_data=NotificationsHourCallbackData(hour=hour)
            )
            for hour in range(24)
        )
        back = Back(text=f"{Emoji.DENIAL} Cancel", callback_data=back_callback_data)

        self.text_message_markup.add_text_row(info)
        self.text_message_markup.add_buttons_in_last_row(*hours)
        self.text_message_markup.attach(back)


class NotificationsMinuteCallbackData(CallbackData, prefix="notification_minute"):
    minute: int


class ChangeNotificationsMinute(InitializeMarkupInterface):
    def __init__(self, back_callback_data: str | CallbackData = "return_to_context"):
        super().__init__()
        info = TextWidget(text=f"{Emoji.CLOCK} Choose notification minute")
        minutes = (
            ButtonWidget(
                text=str(minute),
                callback_data=NotificationsMinuteCallbackData(minute=minute),
            )
            for minute in range(60)
        )
        back = Back(text=f"{Emoji.DENIAL} Cancel", callback_data=back_callback_data)

        self.text_message_markup.add_text_row(info)
        self.text_message_markup.add_buttons_in_last_row(*minutes)
        self.text_message_markup.attach(back)


class TargetsLeftCallbackData(CallbackData, prefix="left_current_targets_list"):
    page: int


class TargetsRightCallbackData(CallbackData, prefix="right_current_targets_list"):
    page: int


class TargetCallbackData(CallbackData, prefix="current_target"):
    id: int


class TargetsList(AsyncInitializeMarkupInterface):
    _targets_per_page = 5

    def __init__(
        self,
        token: str,
        page: int = 0,
        back_callback_data: str | CallbackData = "profile",
    ):
        super().__init__()
        self._page = page
        self._token = token
        self.back_callback_data = back_callback_data

    async def init(self):
        targets, code = await self._api.get_targets(self._token)
        if code == 200:
            if not targets:
                self.text_message_markup.attach(
                    Info(
                        f"No targets so far {Emoji.CRYING_CAT}",
                        back_callback_data=self.back_callback_data,
                    )
                )
            else:
                completed_targets_all_time = sum(
                    (
                        1
                        for target in targets
                        if target["progress"] == target["border_progress"]
                    )
                )
                progress = TextWidget(
                    text=create_progress_text(
                        completed_targets_all_time,
                        len(targets),
                        progress_element=Emoji.DECIDUOUS_TREE,
                        remaining_element=Emoji.SPROUT,
                    )
                )
                count = 0
                pages = []
                page = []
                for target in targets:
                    button = ButtonWidget(text=target["name"])
                    if target["progress"] == target["border_progress"]:
                        button.mark = Emoji.DECIDUOUS_TREE
                        button.callback_data = CompletedTargetCallbackData(
                            id=target["id"]
                        )
                    else:
                        if target["completed"]:
                            button.mark = Emoji.DROPLET
                        button.callback_data = TargetCallbackData(id=target["id"])

                    if count == self._targets_per_page:
                        count = 0
                        pages.append(page)
                        page = []
                    page.append(button)
                    count += 1
                pages.append(page)

                self.text_message_markup.add_text_row(progress)
                for button in pages[self._page]:
                    self.text_message_markup.add_button_in_new_row(button)

                total_pages = len(pages)

                if len(targets) > self._targets_per_page:
                    self.text_message_markup.attach(
                        LeftBackRight(
                            left_callback_data=TargetsLeftCallbackData(
                                page=(self._page - 1) % total_pages
                            ),
                            right_callback_data=TargetsRightCallbackData(
                                page=(self._page + 1) % total_pages
                            ),
                            back_callback_data=self.back_callback_data,
                        )
                    )
                else:
                    self.text_message_markup.attach(
                        Back(callback_data=self.back_callback_data)
                    )
        else:
            self.text_message_markup.attach(ErrorInfo())
        return self


class Target(AsyncInitializeMarkupInterface):
    def __init__(
        self,
        token: str,
        id_: int,
        back_callback_data: str | CallbackData = "return_to_context",
    ):
        super().__init__()
        self._token = token
        self._id = id_
        self.back_callback_data = back_callback_data

    async def init(self):
        data, code = await self._api.get_target(self._token, self._id)
        if code == 200:
            text_map = [
                TextWidget(text=f"{Emoji.SPROUT} {data['name']}"),
                TextWidget(text=f"{Emoji.LIST_WITH_PENCIL} {data['description']}"),
            ]
            progress = TextWidget(
                text=create_progress_text(
                    data["progress"], data["border_progress"], show_digits=False
                )
                + f"{data['progress']}/{data['border_progress']}"
            )
            done = TextWidget(text=Emoji.DROPLET)
            keyboard_map = [
                [
                    ButtonWidget(
                        text=(
                            f"Mark as undone {Emoji.DENIAL}"
                            if data["completed"]
                            else f"Mark as done {Emoji.OK}"
                        ),
                        callback_data="invert_completed",
                    )
                ],
                [
                    ButtonWidget(
                        text=f"Change name {Emoji.SPROUT}", callback_data="change_name"
                    ),
                    ButtonWidget(
                        text=f"Change description {Emoji.LIST_WITH_PENCIL}",
                        callback_data="change_description",
                    ),
                ],
                [
                    ButtonWidget(
                        text=f"Delete target {Emoji.DENIAL}",
                        callback_data="delete_target",
                    )
                ],
            ]
            back = Back(callback_data=self.back_callback_data)

            self.text_message_markup.text_map = text_map
            self.text_message_markup.add_text_row(progress)
            if data["completed"]:
                self.text_message_markup.add_text_row(done)
            self.text_message_markup.keyboard_map = keyboard_map
            self.text_message_markup.attach(back)
        else:
            self.text_message_markup.attach(ErrorInfo())
        return self


class CompletedTargetCallbackData(CallbackData, prefix="completed_target"):
    id: int


class CompletedTarget(AsyncInitializeMarkupInterface):
    def __init__(
        self,
        token: str,
        id_: int,
        back_callback_data: str | CallbackData = "return_to_context",
    ):
        super().__init__()
        self._token = token
        self._id = id_
        self.back_callback_data = back_callback_data

    async def init(self):
        data, code = await self._api.get_target(self._token, self._id)
        if code == 200:
            text_map = [
                DataTextWidget(text=f"{Emoji.DART} Name", data=data["name"]),
                DataTextWidget(
                    text=f"{Emoji.LIST_WITH_PENCIL} Description",
                    data=data["description"],
                ),
                DataTextWidget(text=f"{Emoji.ZAP} Days", data=data["border_progress"]),
                DataTextWidget(
                    text=f"{Emoji.SPROUT} Create date",
                    data=f"{data["create_datetime"]}",
                ),
                DataTextWidget(
                    text=f"{Emoji.DECIDUOUS_TREE} Completed date",
                    data=f"{data["completed_datetime"]}",
                ),
            ]
            keyboard_map = [
                [
                    ButtonWidget(
                        text=f"Delete achievement {Emoji.DENIAL}",
                        callback_data="delete_completed_target",
                    )
                ],
            ]
            back = Back(callback_data=self.back_callback_data)

            self.text_message_markup.text_map = text_map
            self.text_message_markup.keyboard_map = keyboard_map
            self.text_message_markup.attach(back)
        else:
            self.text_message_markup.attach(ErrorInfo())
        return self


class InputBorder(InitializeMarkupInterface):
    def __init__(self, back_callback_data: str | CallbackData = "return_to_context"):
        super().__init__(States.input_text_target_border)
        text = TextWidget(
            text=f"How many days do you want to set for border progress? {Emoji.FLAG_FINISH}\n"
            "(By default border is 21 days. This is standard value for habit fix)"
        )
        skip = ButtonWidget(
            text=f"{Emoji.SKIP} Skip", callback_data="conform_create_target"
        )
        back = Back(text=f"{Emoji.DENIAL} Cancel", callback_data=back_callback_data)

        self.text_message_markup.add_text_row(text)
        self.text_message_markup.add_button_in_new_row(skip)
        self.text_message_markup.attach(back)

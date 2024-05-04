from aiogram.fsm.context import FSMContext
from aiohttp import ClientSession
from apscheduler.triggers.cron import CronTrigger

from frontend import Emoji, scheduler
from frontend.markups.core import *


class BasicManager:
    def __init__(self, interface: Interface):
        self._interface = interface

        self.title_screen = TitleScreen(interface)
        self.profile = Profile(interface)
        self.options = Options(interface)


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
                        "habits": ButtonWidget(text=f"{Emoji.DIAGRAM} Targets", callback_data="habits"),
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
                            text=f"{Emoji.KEY}{Emoji.DENIAL} Remove password",
                            callback_data="delete_password",
                            active=False
                        ),
                    },
                    {
                        "notifications": ButtonWidget(
                            text=f"{Emoji.BELL + Emoji.CLOCK} Change notification time",
                            callback_data="change_notification"
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
                ]
            )
        )


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
                ]
            )
        )


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
                        "sign_in": ButtonWidget(text=f'{Emoji.DOOR}', callback_data='try_profile'),
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
                await self._interface.auth_manager.authorization_with_password.open(state)
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

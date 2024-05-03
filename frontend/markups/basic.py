from aiogram.fsm.context import FSMContext
from aiohttp import ClientSession

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

    async def open(self, state):
        self.text_map['hello'].data = self._interface.first_name
        await super().open(state)


class Options(TextMarkup):
    def __init__(self, interface: Interface):
        super().__init__(
            interface,
            TextMap(
                {
                    "action": TextWidget(f'{Emoji.GEAR️} Choose option')
                }
            ),
            MarkupMap(
                [
                    {
                        "update_password": ButtonWidget(
                            text=f"{Emoji.KEY}{Emoji.PLUS} Add password",
                            callback_data="update_password"
                        ),
                        "delete_password": ButtonWidget(
                            text=f"{Emoji.KEY}{Emoji.DENIAL} Remove password",
                            callback_data="delete_password",
                            active=False
                        ),
                    },
                ]
            )
        )

    async def open(self, state):
        self.markup_map['update_password'].text = f'{Emoji.KEY}{Emoji.UP} Update password'
        await super().open(state)


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

from typing import List
from aiogram.fsm.context import FSMContext
from aiohttp import ClientSession

from config import Emoji
from frontend.markups import Markup, ButtonWidget, CommonButtons, DataTextWidget, TextWidget
from frontend.markups.habits import Habits
from frontend.markups.interface import Interface
from frontend.markups.auth import InputNewPassword, SignInWithPassword


class Profile(Markup):
    def __init__(self, interface: Interface):
        super().__init__(interface)

    def _init_text_map(self):
        self._text_map = {
            "hello": DataTextWidget('Hello', sep=', '),
        }

    def _init_markup_map(self):
        self._markup_map = [
            {
                "habits": ButtonWidget(f"{Emoji.DIAGRAM} Show up current targets", "habits"),
                "create_habit": ButtonWidget(f'f{Emoji.SPROUT} Create new target', 'create_habit')
            },
            {
                "update_password": ButtonWidget(f"{Emoji.KEY} Add password", "update_password")
            },
            {
                "title_screen": ButtonWidget(f'{Emoji.BACK} Exit', "title_screen")
            }
        ]

    async def open(self, state):
        await self._text_map['hello'].update_text(data=self._interface.first_name)
        await super().open(state)

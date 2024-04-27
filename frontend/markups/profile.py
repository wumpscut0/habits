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
        super().__init__()
        self._interface = interface

    def _init_text_map(self):
        self._text_map = {
            "hello": DataTextWidget('Hello', sep=', '),
        }

    def _init_markup_map(self):
        self._markup_map = [
            {
                "habits": ButtonWidget("🧠 Habits", "habits")
            },
            {
                "update_password": ButtonWidget("🔑 Add password", "input_new_password")
            },
            {
                "exit": ButtonWidget(f'{Emoji.BACK} Exit', "title_screen")
            }
        ]

    async def open_profile(self, name, state):
        await self._text_map['hello'].update_text(data=name)
        await self._interface.update(state, self)

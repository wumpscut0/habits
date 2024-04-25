from typing import List

from aiogram.fsm.context import FSMContext
from aiohttp import ClientSession


from frontend.markups import Markup, ButtonWidget, CommonButtons, DataTextWidget, TextWidget
from frontend.markups.habits import Habits
from frontend.markups.interface import Interface
from frontend.markups.password import InputPassword, SignInWithPassword


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
                "habits": ButtonWidget("🧠 Habits", "open_habits")
            },
            {
                "update_password": ButtonWidget("🔑 Add password", "open_input_password")
            },
            {
                "exit": ButtonWidget(f'{BACK} Exit', "open_input_password", active=False)
            }
        ]

    def on_exit_button(self):
        self._markup_map[2]['exit'].on()
        return self

    async def open_session(self, state: FSMContext, name):
        await self._text_map['hello'].update_text(data=name)
        await self._interface.update_current_markup(state, )

    async def open_session_with_password(self, state: FSMContext, session: ClientSession):

    async def update_hello(self, name):

        return self




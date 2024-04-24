from typing import List

from frontend.markups import Markup, ButtonWidget, CommonButtons, DataTextWidget, TextWidget
from frontend.markups.habits import Habits
from frontend.markups.password import InputPassword, SignInPassword


class Profile(Markup):
    def __init__(self):
        super().__init__()

    def _init_related_markups(self):
        self._input_password = InputPassword()
        self._sign_in_password = SignInPassword()
        self._habits = Habits()

    def _init_text_map(self):
        self._text_map = {
            "hello": DataTextWidget('Hello', sep=', ')
        }

    def _init_markup_map(self):
        self._markup_map = [
            {
                "habits": ButtonWidget("🧠 Habits", "open_habits")
            },
            {
                "update_password": ButtonWidget("🔑 Add password", "open_input_password")
            },
        ]

    @property
    def habit(self):
        return self._habit

    @property
    def input_password(self):
        return self._input_password

    @property
    def sign_in_with_password(self):
        return self._sign_in_password

    def add_exit_button(self):
        self._text_map['back'] = CommonButtons.back('open_input_password', text='Exit')
        return self

    async def update_hello(self, name):
        await self._text_map['hello'].update_text(data=name)
        return self




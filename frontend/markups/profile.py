from frontend.markups import Markup, ButtonWidget, CommonButtons, DataTextWidget
from frontend.markups.password import InputPassword, SignInPassword


class Profile(Markup):
    def __init__(self):
        super().__init__()
        # self._habit = Habit()
        self._header = DataTextWidget('Hello, ')
        self._input_password = InputPassword()
        self._sign_in_password = SignInPassword()
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

    async def set_hello(self, name):
        self._header.header = f'Hello, {name}'
        return self




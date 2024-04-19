from aiogram.utils.formatting import Bold


from frontend.markups import Markup, ButtonWidget
from frontend.markups.sign_up import SignUp


class Authorization(Markup):
    def __init__(self):
        super().__init__()
        self._header = '🧠 Psychological service'
        # self._sign_in = SignIn()
        self._sign_up = SignUp()
        self._markup_map = [
            {
                "sign_in": ButtonWidget("🔐 Login", "open_sign_in")
            },
            {
                "sign_up": ButtonWidget("🔓🔑 Sign up", "open_sign_up")
            }
        ]

    @property
    def sign_up(self):
        return self._sign_up

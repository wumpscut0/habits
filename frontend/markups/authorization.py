from frontend.markups import Markup


class Authorization(Markup):
    def __init__(self):
        super().__init__()
        self._header = '🧠 Psychological service'
        self._markup_map = [
            [
                {"mark": "🔐 ", "text": "Login", "callback_data": "authorization_login"}
            ],
            [
                {"mark": "🔓🔑 ", "text": "Sign in", "callback_data": "sign_in"}
            ]
        ]

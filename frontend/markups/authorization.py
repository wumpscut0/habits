from frontend.markups import Markup, ButtonWidget


class Authorization(Markup):
    def __init__(self):
        super().__init__()
        self._header = '🧠 Psychological service'
        self._markup_map = [
            {
                "login": ButtonWidget("🔐 Login", "authorization_login")
            },
            {
                "sign_in": ButtonWidget("🔓🔑 Sign up", "sign_up")
            }
        ]

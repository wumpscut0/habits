import re
from config import *
from frontend.markups import Markup, CommonTexts, CommonButtons


class Nickname(Markup):
    def __init__(self):
        super().__init__()
        self._nickname = None

        self._header = "🪪 Enter the nickname"
        self._text_map = {
            'nickname': CommonTexts.nickname(),
            'feedback': CommonTexts.feedback(),
        }
        self._markup_map = [
            {
                'accept': CommonButtons.accept('open_sign_up')
            },
        ]

    @property
    def nickname(self):
        return self._nickname

    async def update_nickname(self, nickname):
        if not re.fullmatch(r'\w{3,10}', nickname, flags=re.I):
            await self._text_map['feedback'].update_text(
                data=f"Nickname {nickname} not allowed."
                     " Nickname must contains only latin symbols or signs '_' or digits.",
                mark=DENIAL
            )
        else:
            self._nickname = nickname
            await self._text_map['nickname'].update_text(data=nickname)
            await self._text_map['feedback'].update_text(data="Nickname allowed", mark=OK)

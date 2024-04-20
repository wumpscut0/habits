import json
import os
import jwt
from aiohttp import ClientSession

from frontend import errors
from frontend.markups import Markup, ButtonWidget, CommonButtons, CommonTexts
from frontend.markups.login import Login
from frontend.markups.nickname import Nickname
from frontend.markups.password import Password


class Profile(Markup):
    """
    Data in database and data in redis will be merged every sign in
    """
    def __init__(self):
        super().__init__()

        self._markup_map = [
            {
                'back': CommonButtons.back('open_authorization')
            }
        ]

    async def merge_nickname(self, nickname):
        if self._text_map.get('nickname') is None:
            self._text_map['nickname'] = CommonTexts.nickname()

        await self._text_map['nickname'].update_text(data=nickname)

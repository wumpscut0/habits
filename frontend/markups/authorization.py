from frontend.markups import Markup, ButtonWidget
from frontend.markups.password import InputPassword


class Profile(Markup):
    def __init__(self):
        super().__init__()
        # self._habit = Habit()
        self._input_password = InputPassword()
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


# import json
# import os
# import jwt
# from aiohttp import ClientSession
#
# from frontend import errors
# from frontend.markups import Markup, ButtonWidget, CommonButtons, CommonTexts
# from frontend.markups.login import Login
# from frontend.markups.nickname import Nickname
# from frontend.markups.password import AddPassword
#
#
# class Profile(Markup):
#     """
#     Data in database and data in redis will be merged every sign in
#     """
#     def __init__(self):
#         super().__init__()
#
#         self._markup_map = [
#             {
#                 'back': CommonButtons.back('open_authorization')
#             }
#         ]
#
#     async def merge_nickname(self, nickname):
#         if self._text_map.get('nickname') is None:
#             self._text_map['nickname'] = CommonTexts.nickname()
#
#         await self._text_map['nickname'].update_text(data=nickname)




from passlib.handlers.pbkdf2 import pbkdf2_sha256
from zxcvbn import zxcvbn
from config import *
from frontend.markups import Markup, CommonTexts, TextWidget, CommonButtons, ButtonWidget


class Password(Markup):
    _strength_marks = {
        4: '🟢 Reliable',
        3: '🟡 Good',
        2: '🟠 Medium',
        1: '🔴 Bad',
        0: '⚠️ Terrible'
    }

    def __init__(self):
        super().__init__()
        self._password = None
        self._repeat_password = None
        self._hash = None

        self._header = 'Enter the password'
        self._text_map = {
            "password": CommonTexts.password(),
            "repeat_password": TextWidget("🔑 Repeat password"),
            "strength": TextWidget("🛡️ Strength"),
            "warning": TextWidget("⚠️ Warning"),
            "suggestions": TextWidget("🌟 Suggestions"),
            "feedback": CommonTexts.feedback(),
        }
        self._markup_map = [
            {
                "accept": CommonButtons.accept("open_sign_up")
            },
            {
                "input_mode": ButtonWidget("🔄 Input mode", "mode_password"),
            },
        ]

    @property
    def password(self):
        return '*' * len(self._password)

    @property
    def hash(self):
        return self._hash

    async def invert_input_mode(self):
        if self._header == 'Enter the password':
            self._header = "Repeat the password"
        else:
            self._header = 'Enter the password'

    async def update_password(self, password):
        self._hash = None
        self._text_map['password'].reset()
        if len(password) > PASSWORD_LENGTH:
            await self._text_map['feedback'].update_text(data=f"Maximum password length is {PASSWORD_LENGTH} symbols")
        else:
            password_grade = zxcvbn(password)
            warning = password_grade['feedback'].get('warning')
            suggestions = password_grade['feedback'].get('suggestions')

            self._password = password
            await self._text_map['password'].update_text(data=self.password)
            self._text_map['repeat_password'].reset()
            await self._text_map['strength'].update_text(data=self._strength_marks[password_grade['score']])
            warning = warning if warning is not None else OK
            await self._text_map['warning'].update_text(data=warning)
            suggestions = "\n" + "\n".join(suggestions) if suggestions is not None else OK
            await self._text_map['suggestions'].update_text(data=suggestions)

            await self.invert_input_mode()

    async def repeat_password(self, password):
        if len(password) > PASSWORD_LENGTH:
            await self._text_map['feedback'].update_text(data=f"Maximum password length is {PASSWORD_LENGTH} symbols")
        else:
            self._repeat_password = password
            if password != self._password:
                await self._text_map['password'].update_text(mark=DENIAL)
                await self._text_map['repeat_password'].update_text(data='*' * len(password), mark=DENIAL)
                await self._text_map['feedback'].update_text(data="Passwords not matched")
            else:
                await self._text_map['password'].update_text(mark=OK)
                await self._text_map['repeat_password'].update_text(data='*' * len(password), mark=OK)
                await self._text_map['feedback'].update_text(data="Passwords matched")
                self._hash = pbkdf2_sha256.hash(password)

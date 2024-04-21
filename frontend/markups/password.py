from aiogram.fsm.context import FSMContext
from passlib.handlers.pbkdf2 import pbkdf2_sha256
from zxcvbn import zxcvbn
from config import *

from frontend.markups import Markup, CommonTexts, TextWidget, CommonButtons, ButtonWidget
from frontend.markups.interface import States


class InputPassword(Markup):
    _strength_marks = {
        4: '🟢 Reliable',
        3: '🟡 Good',
        2: '🟠 Medium',
        1: '🔴 Bad',
        0: '⚠️ Terrible'
    }
    state = States.input_password

    def __init__(self):
        super().__init__()
        self._password_resume = PasswordResume()

        self._password = None
        self._hash = None

        self._header = 'Enter the password'
        self._text_map = {
            "feedback": CommonTexts.feedback()
        }
        self._markup_map = [
            {
                "back": CommonButtons.back("open_profile")
            }
        ]

    @property
    def password_resume(self):
        return self._password_resume

    async def input_password(self, password):
        if len(password) > PASSWORD_LENGTH:
            await self._text_map['feedback'].update_text(data=f"Maximum password length is {PASSWORD_LENGTH} symbols")
        else:
            self.state = States.repeat_password

            self._header = 'Repeat the password'

            self._password = password

            resume_map = self._password_resume.text_map

            password_grade = zxcvbn(password)
            warning = password_grade['feedback'].get('warning')
            warning = warning if warning is not None else OK
            suggestions = password_grade['feedback'].get('suggestions')
            suggestions = "\n" + "\n".join(suggestions) if suggestions is not None else OK

            await resume_map['strength'].update_text(data=self._strength_marks[password_grade['score']])
            await resume_map['warning'].update_text(data=warning)
            await resume_map['suggestions'].update_text(data=suggestions)
        return self

    async def repeat_password(self, password):
        if password != self._password:
            self.state = States.input_password

            await self._password_resume.reset()
            await self._text_map['feedback'].update_text(data="Passwords not matched")
            return self
        else:
            self._hash = pbkdf2_sha256.password(password)
            return self._password_resume


class PasswordResume(Markup):
    def __init__(self):
        super().__init__()
        self._password = None
        self._repeat_password = None
        self._hash = None

        self._header = '🔑 Enter the password'
        self._text_map = {
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
                "input_mode": CommonButtons.invert_mode("mode_password"),
            },
        ]

    @property
    def password(self):
        return '*' * len(self._password)

    @property
    def hash(self):
        return self._hash

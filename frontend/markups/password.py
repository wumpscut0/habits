from aiohttp import ClientSession
from passlib.handlers.pbkdf2 import pbkdf2_sha256
from zxcvbn import zxcvbn
from config import OK, DENIAL, PASSWORD_LENGTH
from frontend import info
from frontend.FSM import States, StateManager
from frontend.markups import Markup, CommonTexts, CommonButtons, ButtonWidget, DataTextWidget, TextWidget


class InputPassword(Markup):
    _strength_marks = {
        4: '🟢 Reliable',
        3: '🟡 Good',
        2: '🟠 Medium',
        1: '🔴 Bad',
        0: '⚠️ Terrible'
    }

    def __init__(self):
        super().__init__()

    def _init_state(self):
        self._state_manager = StateManager(States.input_password)

    def _init_related_markups(self):
        self._password_resume = PasswordResume()

    def _init_data(self):
        self._password = None
        self._hash = None

    def _init_text_map(self):
        self._text_map = {
            "feedback": CommonTexts.feedback(),
            "action": TextWidget('Enter the password')
        }

    def _init_markup_map(self):
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
            self._state_manager.state = States.repeat_password

            self._text_map['action'].text = 'Repeat the password'

            self._password = password

            resume_map = self._password_resume.text_map

            password_grade = zxcvbn(password)
            warning = password_grade['feedback']['warning']
            warning = warning if warning else OK

            suggestions = '\n'
            for n, suggestion in enumerate(password_grade['feedback']['suggestions'], start=1):
                suggestions += f'{n}) {suggestion}'

            if suggestions == '\n':
                suggestions = OK

            await resume_map['strength'].update_text(data=self._strength_marks[password_grade['score']])
            await resume_map['warning'].update_text(data=warning)
            await resume_map['suggestions'].update_text(data=suggestions)
            info.info(f"Password Resume text map: {resume_map}")
        return self

    async def repeat_password(self, password):
        self._state_manager.state = States.input_password
        await self.reset()
        if password != self._password:
            await self._password_resume.reset()
            await self._text_map['feedback'].update_text(data="Passwords not matched")
            return self
        else:
            self._hash = pbkdf2_sha256.hash(password)
            return self._password_resume

    @property
    def hash(self):
        self._password = None
        return self._hash


class PasswordResume(Markup):
    def __init__(self):
        super().__init__()

    def _init_related_markups(self):
        self._password_warning = PasswordWarning()

    def _init_text_map(self):
        self._text_map = {
            "info": TextWidget('Password grade'),
            "strength": DataTextWidget("🛡️ Strength"),
            "warning": DataTextWidget("⚠️ Warning"),
            "suggestions": DataTextWidget("🌟 Suggestions"),
            "feedback": CommonTexts.feedback(),
        }

    def _init_markup_map(self):
        self._markup_map = [
            {
                "accept": CommonButtons.accept("open_warning")
            },
            {
                "cancel": ButtonWidget(f'{DENIAL} Cancel', "open_profile")
            }
        ]

    @property
    def password_warning(self):
        return self._password_warning


class PasswordWarning(Markup):
    def __init__(self):
        super().__init__()

    def _init_text_map(self):
        self._text_map = {
            "warning": TextWidget('⚠️ Warning. If you forget password. Access to account data will be lost forever')
        }

    def _init_markup_map(self):
        self._markup_map = [
            {
                "understand": ButtonWidget(f"{OK} I understand", "update_password"),
                "cancel": ButtonWidget(f'{DENIAL} Cancel', 'open_warning')
            }
        ]


class SignInPassword(Markup):
    def __init__(self):
        super().__init__()

    def _init_state(self):
        self._state = States.sign_in_with_password

    def _init_text_map(self):
        self._text_map = {
            "info": TextWidget('🔑 Enter the password'),
            "feedback": CommonTexts.feedback()
        }

    async def sign_in_with_password(self, session: ClientSession, password: str, telegram_id: int) -> str | None:
        async with session.get('sign_in', json={'telegram_id': telegram_id, "password": password}) as response:
            if response.status == 200:
                return (await response.json())['token']
            else:
                await self._text_map['feedback'].update_text(data='Wrong password')

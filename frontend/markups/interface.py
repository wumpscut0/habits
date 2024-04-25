from typing import Any, Dict

from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext

from frontend import bot
from frontend.markups import SerializableMixin, Markup
from frontend.markups.password import InputPassword, SignInWithPassword, PasswordResume, InputEmail, RepeatPassword
from frontend.markups.profile import Profile
from frontend.markups.sign_in import SignIn


class Interface(SerializableMixin):
    def __init__(self, chat_id: int):
        self.sign_in = SignIn(self)
        self.profile = Profile(self)
        self.input_password = InputPassword(self)
        self.repeat_password = RepeatPassword(self)
        self.password_resume = PasswordResume(self)
        self.input_email = InputEmail(self)
        self.sign_in_password = SignInWithPassword(self)

        self._chat_id = chat_id

        self._current_markup = None
        self._trash = []

        self._token = None
        self._message_id = None

    # def __getitem__(self, item):
    #     return self._markups[item]
    #
    # def __setitem__(self, key, value):
    #     self._markups[key] = value

    def __getattr__(self, item: str) -> Any:
        if item in self._data:
            return self._data[item]
        raise AttributeError(f"'CustomDict' object has no attribute '{item}'")

    @property
    def current_markup(self) -> Markup:
        return self._current_markup

    async def update_current_markup(self, state: FSMContext, markup: Markup):
        self._current_markup = markup
        await state.set_state(markup.state)
        await self._update_interface_in_redis(state)
        await bot.edit_message_text(
            chat_id=self._chat_id,
            message_id=self._message_id,
            text=await markup.text,
            reply_markup=await markup.markup
        )
        await self.clean_trash()

    @property
    def chat_id(self):
        return self._chat_id

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, token):
        self._token = token

    async def close_session(self, state, msg='Session close'):
        await state.set_state(None)
        try:
            message = await bot.edit_message_text(
                chat_id=self._chat_id,
                message_id=self._message_id,
                text=msg
            )
            self._trash.append(message.message_id)
        except TelegramBadRequest:
            return 'Open session not found'

        await self._update_interface_in_redis(state)

    async def open_session(self, state):
        await state.set_state(None)

        message = await bot.send_message(
            chat_id=self._chat_id,
            text=await self.sign_in.text,
            reply_markup=await self.sign_in.markup
        )
        self._message_id = message.message_id

        await self._update_interface_in_redis(state)

    async def _update_interface_in_redis(self, state):
        await state.update_data({'interface': await self.serialize()})

    async def clean_trash(self):
        for message_id in self._trash:
            try:
                await bot.delete_message(self._chat_id, message_id)
            except TelegramBadRequest:
                try:
                    await bot.edit_message_text('deleted', self._chat_id, message_id)
                except TelegramBadRequest:
                    pass
        self._trash = []

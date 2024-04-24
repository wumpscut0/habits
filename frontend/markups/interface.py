from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext

from frontend import bot
from frontend.markups import SerializableMixin, Markup
from frontend.markups.password import InputPassword, SignInPassword, PasswordWarning
from frontend.markups.profile import Profile


class Interface(SerializableMixin):
    def __init__(self, chat_id: int):
        self._markups = {
            "profile": Profile(self),
            "input_password": InputPassword(self),
            "warning_password": PasswordWarning(self),
            "sign_in_password": SignInPassword(self),

        }
        self._chat_id = chat_id

        self._current_markup = None
        self._trash = []

        self._token = None
        self._message_id = None

    def __getitem__(self, item):
        return self._markups[item]

    def __setitem__(self, key, value):
        self._markups[key] = value

    @property
    def current_markup(self) -> Markup:
        return self._current_markup

    async def update_current_markup(self, state: FSMContext, markup: str):
        markup = self._markups[markup]
        self._current_markup = markup
        await state.set_state(markup.state)
        await self._update_interface_in_redis(state)
        await bot.edit_message_text(chat_id=self._chat_id, message_id=self._message_id, text=await markup.text,
                                    reply_markup=await markup.markup)
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

    async def open_session(self, state, markup: Markup):
        await state.set_state(None)

        message = await bot.send_message(
            chat_id=self._chat_id,
            text=await markup.text,
            reply_markup=await markup.markup
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

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from frontend.markups import SerializableMixin, Markup
from frontend.markups.authorization import Profile
from aiogram.fsm.state import State, StatesGroup


class States(StatesGroup):
    input_password = State()
    repeat_password = State()


class Interface(SerializableMixin):
    def __init__(self, bot: Bot, chat_id: int, state: FSMContext):
        self._profile = Profile()
        self._bot = bot
        self._chat_id = chat_id
        self._state = state
        self._trash = []

        self._token = None
        self._message: Message | None = None

    @property
    def profile(self):
        return self._profile

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, token):
        self._token = token

    async def open_session(self):
        await self._state.set_state(None)

        if self._message is not None:
            try:
                message = await self._bot.edit_message_text(
                    chat_id=self._chat_id,
                    message_id=self._message.message_id,
                    text='Session close'
                )
                self._trash.append(message.message_id)
            except TelegramBadRequest:
                return 'Open session not found'

        self._message = await self._bot.send_message(
            chat_id=self._chat_id,
            text=await self._profile.text,
            reply_markup=await self._profile.markup
        )

        await self._update_interface_in_redis()

    async def update_interface(self, markup: Markup):
        await self._state.set_state(markup.state)
        await self._update_interface_in_redis()
        await self._message.edit_text(text=await markup.text, reply_markup=await markup.markup)
        await self._clean_trash()

    async def _update_interface_in_redis(self):
        await self._state.update_data({'interface': await self.serialize()})

    async def _clean_trash(self):
        for message_id in self._trash:
            await self._bot.delete_message(self._chat_id, message_id)
        self._trash = []

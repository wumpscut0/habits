from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from frontend import bot
from frontend.markups.auth import AuthManager
from frontend.markups.core import SerializableMixin, Markup
from frontend.markups.targets import CreateHabitName, CreateTargetBorder, TargetsManager, ShowUpHabitsTemp, HabitControlTemp
from frontend.markups.profile import Profile
from frontend.markups.title_screen import TitleScreen


class Interface(SerializableMixin):
    def __init__(self, chat_id: int, first_name: str):
        self.markup = Markup

        self.basic_manager = BasicManager(self)
        self.auth_manager = AuthManager(self)
        self.targets_manager = TargetsManager(self)

        self.first_name = first_name
        self.chat_id = chat_id

        self._current_markup = None

        self._trash = []

        self.token = None
        self._message_id = None

    async def open_session(self, state, close_msg='Session close'):
        await self._reset_state(state)

        try:
            message = await bot.edit_message_text(
                chat_id=self.chat_id,
                message_id=self._message_id,
                text=close_msg
            )
            self._trash.append(message.message_id)
        except TelegramBadRequest:
            return 'Open session not found'

        message = await bot.send_message(
            chat_id=self.chat_id,
            text=await self.title_screen.text,
            reply_markup=await self.title_screen.markup
        )
        self._message_id = message.message_id

        await self._update_interface_in_redis(state)

    async def close_session(self, state):
        await self._reset_state(state)
        await self.title_screen.open(state)

    async def update(self, state: FSMContext, markup: Markup):
        self._current_markup = markup
        await state.set_state(markup.state)
        await self._update_interface_in_redis(state)
        await bot.edit_message_text(
            chat_id=self.chat_id,
            message_id=self._message_id,
            text=await markup.text,
            reply_markup=await markup.markup
        )
        await self.clean_trash()

    async def clean_trash(self):
        for message_id in self._trash:
            try:
                await bot.delete_message(self.chat_id, message_id)
            except TelegramBadRequest:
                try:
                    await bot.edit_message_text('deleted', self.chat_id, message_id)
                except TelegramBadRequest:
                    pass
        self._trash = []

    async def refill_trash(self, message_id: int):
        self._trash.append(message_id)

    async def handling_unexpected_error(self, state):
        await self.markup.update_feedback('Internal server error.')
        await self._current_markup.open(state)

    async def _reset_state(self, state: FSMContext):
        await state.set_state(None)
        self.token = None

    async def _update_interface_in_redis(self, state):
        await state.update_data({'interface': await self.serialize()})



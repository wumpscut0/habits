import os

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BotCommand

from client.api import ServerApi
from client.markups.core import TextMessageMarkup
from client.utils import Emoji
from client.utils.loggers import errors
from client.utils.redis import Storage


class BotCommands:
    bot_commands = [
        BotCommand(
            command="/start",
            description="Get title screen"
        ),
        BotCommand(
            command="/exit",
            description="Close interface"
        ),
        BotCommand(
            command="/jobs",
            description="Show current tasks"
        )
    ]

    @classmethod
    def start(cls):
        return Command(cls.bot_commands[0].command.lstrip('/'))

    @classmethod
    def exit(cls):
        return Command(cls.bot_commands[1].command.lstrip('/'))

    @classmethod
    def jobs(cls):
        return Command(cls.bot_commands[2].command.lstrip('/'))


class BotControl:
    bot = Bot(os.getenv('TOKEN'), parse_mode='HTML')
    api = ServerApi()

    def __init__(self, user_id: int, state: FSMContext | None = None):
        self._user_id = user_id
        self.state = state
        self.storage = Storage(user_id)

    @property
    def user_id(self):
        return str(self._user_id)

    async def create_text_message(self, text_message_markup: TextMessageMarkup, contextualize=True, context=True):
        if context:
            self.storage.current_text_message_markup = text_message_markup

        if contextualize:
            await self._contextualize_chat()

        if self.state is not None:
            await self.state.set_state(text_message_markup.state)

        try:
            message = await self.bot.send_message(
                chat_id=self._user_id,
                text=text_message_markup.text,
                reply_markup=text_message_markup.keyboard
            )
            self.storage.add_message_id_to_the_pull(message.message_id)
        except TelegramBadRequest:
            errors.critical("Unsuccessfully creating text message.")

    async def update_text_message(self, text_message_markup: TextMessageMarkup, contextualize=True, context=True):
        if context:
            self.storage.current_text_message_markup = text_message_markup

        if contextualize:
            await self._contextualize_chat()

        if self.state is not None:
            await self.state.set_state(text_message_markup.state)

        last_message_id = self.storage.last_message_id
        if last_message_id is None:
            await self.create_text_message(text_message_markup)
            return

        try:
            await self.bot.edit_message_text(
                chat_id=self._user_id,
                message_id=last_message_id,
                text=text_message_markup.text,
                reply_markup=text_message_markup.keyboard
            )

        except TelegramBadRequest:
            await self.delete_message(last_message_id)
            self.storage.pop_last_message_id_from_the_pull()
            await self.update_text_message(text_message_markup)

    async def refresh_context(self):
        await self.update_text_message(self.storage.current_text_message_markup)

    async def _contextualize_chat(self):
        valuables_messages = []
        for message_id in self.storage.message_ids_pull[:-1]:
            if await self.delete_message(message_id):
                valuables_messages.append(message_id)
        try:
            valuables_messages.append(self.storage.message_ids_pull[-1])
            self.storage.message_ids_pull = valuables_messages
        except IndexError:
            pass

    async def delete_message(self, message_id: int, forced_text=f"{Emoji.FROG}"):
        try:
            await self.bot.delete_message(self._user_id, message_id)
        except TelegramBadRequest:
            try:
                await self.bot.edit_message_text(forced_text, self._user_id, message_id)
                return True
            except TelegramBadRequest:
                pass

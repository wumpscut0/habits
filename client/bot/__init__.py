import os

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BotCommand

from client.api import Api
from client.markups import Info, InitializeMarkupInterface
from client.markups.core import TextMessageMarkup
from client.markups.specific import TitleScreen
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
    ]

    @classmethod
    def start(cls):
        return Command(cls.bot_commands[0].command.lstrip('/'))

    @classmethod
    def exit(cls):
        return Command(cls.bot_commands[1].command.lstrip('/'))


class BotControl:
    bot = Bot(os.getenv('TOKEN'), parse_mode='HTML')
    api = Api()

    def __init__(self, user_id: int, state: FSMContext | None = None):
        self._user_id = user_id
        self.state = state
        self.storage = Storage(user_id)

    @property
    def user_id(self):
        return str(self._user_id)

    async def create_text_message(self, text_message_markup: TextMessageMarkup, contextualize=True, context=True):
        if context:
            self.storage.context = text_message_markup

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

    async def update_text_message(self, text_message_markup: TextMessageMarkup | InitializeMarkupInterface, contextualize=True, context=True):
        if isinstance(text_message_markup, InitializeMarkupInterface):
            text_message_markup = text_message_markup.text_message_markup

        if context:
            self.storage.context = text_message_markup

        if contextualize:
            await self._contextualize_chat()

        if self.state is not None:
            await self.state.set_state(text_message_markup.state)

        last_message_id = self.storage.last_message_id
        if last_message_id is None:
            await self.create_text_message(text_message_markup, context)
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
            await self.update_text_message(text_message_markup, context)

    async def return_to_context(self):
        try:
            await self.update_text_message(self.storage.context)
        except Exception:
            # If we change code with context in redis, then exist chance work this exception
            self.storage.context = await TitleScreen().init(self.user_id)
            await self.update_text_message(Info("Application updated. Please sign in again.").text_message_markup, context=False)

    async def send_message_to_admin(self, message: str):
        await self.bot.send_message(
            chat_id=os.getenv("GROUP_ID"),
            text=f"Reply from {self.storage.first_name}\n"
                 f"{message}",
        )

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

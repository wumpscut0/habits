import os

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import BotCommand
from apscheduler.jobstores.base import JobLookupError
from apscheduler.triggers.cron import CronTrigger

from client.api import ServerApi
from client.markups.core import TextMessage
from client.utils.redis import Storage
from client.utils.scheduler import scheduler, remainder


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

    @property
    def start(self):
        return self.bot_commands[0]

    @property
    def exit(self):
        return self.bot_commands[1]

    @property
    def jobs(self):
        return self.bot_commands[2]

    @classmethod
    def str_commands(cls):
        return ':'.join([command.command for command in cls.bot_commands])


class BotControl:
    bot = Bot(os.getenv('TOKEN'), parse_mode='HTML')
    api = ServerApi()

    def __init__(self, user_id: int, state: FSMContext | None = None):
        super().__init__(self, user_id)
        self._user_id = user_id
        self.state = state
        self.storage = Storage(user_id)

    @property
    def user_id(self):
        return str(self._user_id)

    async def create_interface(self, text_message: TextMessage, clean_trash=True, trash=False, temp=False):
        if not temp:
            self.storage.current_interface = text_message

        if clean_trash:
            await self.clean_trash()

        if self.state is not None:
            await self.state.set_state(text_message.state)

        try:
            message = await self.bot.send_message(
                chat_id=self._user_id,
                text=text_message.text,
                reply_markup=text_message.markup
            )
            if trash:
                self.refill_trash(message.message_id)
            else:
                self.storage.message_id = message.message_id
        except TelegramBadRequest:
            pass

    async def update_interface(self, text_message: TextMessage, clean_trash=True, temp=False):
        if not temp:
            self.storage.current_interface = text_message

        if clean_trash:
            await self.clean_trash()

        if self.state is not None:
            await self.state.set_state(text_message.state)

        try:
            await self.bot.edit_message_text(
                chat_id=self._user_id,
                message_id=self.storage.message_id,
                text=text_message.text,
                reply_markup=text_message.markup
            )
        except TelegramBadRequest:
            pass

    async def delete_interface(self, clean_trash=True):
        self.storage.current_interface = None

        if clean_trash:
            await self.clean_trash()

        if self.state is not None:
            await self.state.set_state(None)

        message_id = self.storage.message_id
        if message_id is not None:
            await self.delete_message(self.storage.message_id)

    async def refresh_interface(self, clean_trash=True):
        if clean_trash:
            await self.clean_trash()

        text_message = self.storage.current_interface

        if self.state is not None:
            await self.state.set_state(text_message.state)

        try:
            await self.bot.edit_message_text(
                chat_id=self._user_id,
                message_id=self.storage.message_id,
                text=text_message.text,
                reply_markup=text_message.markup
            )
        except TelegramBadRequest:
            pass

    async def clean_trash(self):
        for message_id in self.storage.trash:
            await self.delete_message(message_id)
        self.storage.trash = []

    def refill_trash(self, message_id: int):
        trash = self.storage.trash
        trash.append(message_id)
        self.storage.trash = trash

    async def delete_message(self, message_id: int, forced_text="deleted"):
        try:
            await self.bot.delete_message(self._user_id, message_id)
        except TelegramBadRequest:
            try:
                await self.bot.edit_message_text(forced_text, self._user_id, message_id)
            except TelegramBadRequest:
                pass

    async def refresh_notifications(self):
        user_response = await self.api.get_user(self.user_id)
        targets_response = await self.api.get_targets(self.user_id)
        if user_response.status == 200 and targets_response.status == 200:
            user = (await user_response.json())
            targets = (await targets_response.json())
            all_done = True
            for target in targets:
                if not target["completed"]:
                    all_done = False
                    break
            if user["notifications"] and not all_done:
                time_ = user["notification_time"]
                scheduler.add_job(
                    func=remainder,
                    trigger=CronTrigger(hour=time_["hour"], minute=time_["minute"]),
                    args=(self._user_id,), replace_existing=True, id=str(self._user_id)
                )
            else:
                try:
                    scheduler.remove_job(job_id=self._user_id, jobstore='default')
                except JobLookupError:
                    pass

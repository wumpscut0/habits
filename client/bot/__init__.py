import os

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from aiohttp import ContentTypeError
from apscheduler.jobstores.base import JobLookupError
from apscheduler.triggers.cron import CronTrigger

from client.api import ServerApi
from client.markups.basic import TitleScreen
from client.markups.core import DataTextWidget, TextMessage, TextMap, MarkupMap
from client.utils import Emoji
from client.utils.loggers import errors
from client.utils.redis import Storage
from client.utils.scheduler import scheduler, remainder


class BotControl:
    bot = Bot(os.getenv('TOKEN'), parse_mode='HTML')
    server_api = ServerApi()

    def __init__(self, user_id: int, state: FSMContext):
        super().__init__(self, user_id)
        self.user_id = user_id
        self.state = state
        self.storage = Storage(user_id)

    async def create_interface(self, text_map: TextMap, markup_map: MarkupMap = None, clean_trash=True):
        if clean_trash:
            await self.clean_trash()

        await self.state.set_state(None)

        try:
            message = await self.bot.send_message(
                chat_id=self.user_id,
                text=text_map.text,
                reply_markup=None if markup_map is None else markup_map.markup
            )
            self.storage.message_id = message.message_id
        except TelegramBadRequest:
            pass

    async def update_interface(self, text_map: TextMap, markup_map: MarkupMap = None, state: State | None = None, clean_trash=True):
        if clean_trash:
            await self.clean_trash()

        await self.state.set_state(state)

        try:
            await self.bot.edit_message_text(
                chat_id=self.user_id,
                message_id=self.storage.message_id,
                text=text_map.text,
                reply_markup= None if markup_map is None else markup_map.markup
            )
        except TelegramBadRequest:
            pass

    async def temp_update_interface(self, msg="Processing..."):
        try:
            await self.bot.edit_message_text(text=msg, chat_id=self.user_id, message_id=self.storage.message_id)
        except TelegramBadRequest:
            pass

    async def delete_interface(self, clean_trash=True):
        if clean_trash:
            await self.clean_trash()

        await self.state.set_state(None)

        await self.delete_message(self.storage.message_id)

    async def clean_trash(self):
        for message_id in self.storage.trash:
            await self.delete_message(message_id)
        self.storage.trash = []

    async def refill_trash(self, message_id: int):
        trash = self.storage.trash
        trash.append(message_id)
        self.storage.trash = trash

    async def delete_message(self, message_id, forced_text="deleted"):
        try:
            await self.bot.delete_message(self.user_id, message_id)
        except TelegramBadRequest:
            try:
                await self.bot.edit_message_text(forced_text, self.user_id, message_id)
            except TelegramBadRequest:
                pass

    async def refresh_notifications(self):
        user_response = await self.server_api.get_user()
        targets_response = await self.server_api.get_targets()
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
                    args=(self.user_id,), replace_existing=True, id=str(self.user_id)
                )
            else:
                try:
                    scheduler.remove_job(job_id=self.user_id, jobstore='default')
                except JobLookupError:
                    pass

from typing import Literal

from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiohttp import ClientSession, ContentTypeError
from aiohttp.web_response import Response
from apscheduler.jobstores.base import JobLookupError
from apscheduler.triggers.cron import CronTrigger
from pydantic import ValidationError

from frontend.bot import bot
from frontend.markups.basic import BasicManager
from frontend.markups.core import TextMarkup, DataTextWidget
from frontend.markups.targets import TargetsManager
from frontend.utils import SerializableMixin, Emoji, encode_jwt, storage
from frontend.utils.loggers import errors, info
from frontend.utils.scheduler import scheduler, remainder


class Interface(SerializableMixin):
    _feedback_headers = {
        "default": f'{Emoji.REPORT} Feedback',
        "info": f"{Emoji.INFO} Info",
        "error": f"{Emoji.DENIAL} Error"
    }

    def __init__(self, chat_id: int, first_name: str):
        self.basic_manager = BasicManager(self)
        self.targets_manager = TargetsManager(self)

        self.first_name = first_name
        self.chat_id = chat_id
        self.token = None
        self.feedback = DataTextWidget(active=False)

        self.state = None
        self.session = None

        self._current_markup = None
        self._trash = []

    async def reset_session(self, close_msg='Session close'):
        await self._reset_state()
        message_id = storage.get(f"{self.chat_id}")
        try:
            message = await bot.edit_message_text(
                chat_id=self.chat_id,
                message_id=message_id,
                text=close_msg
            )
            self._trash.append(message.message_id)
        except TelegramBadRequest:
            pass

        async with self.session.get(f'/notification_is_on/{await encode_jwt({"telegram_id": self.chat_id})}') as response:
            response_ = await response.text()
            if response_ == '1':
                self.basic_manager.title_screen.markup_map["notifications"].mark = Emoji.BELL
            elif response_ == '0':
                self.basic_manager.title_screen.markup_map["notifications"].mark = Emoji.NOT_BELL
            else:
                self.basic_manager.title_screen.markup_map["notifications"].mark = Emoji.RED_QUESTION
                errors.error(f'Unsuccessfully check notification, return code: {response.status}')

        message = await bot.send_message(
            chat_id=self.chat_id,
            text=await self.basic_manager.title_screen.text,
            reply_markup=await self.basic_manager.title_screen.markup
        )

        storage.set(f"{self.chat_id}", message.message_id)

        await self.update_interface_in_redis()

    async def close_session(self):
        await self._reset_state()
        await self.basic_manager.title_screen.open()

    async def clear(self, state):
        message_id = storage.get(f"{self.chat_id}")
        if self.chat_id is not None and message_id is not None:
            await bot.delete_message(chat_id=self.chat_id, message_id=message_id)
        await self.clean_trash()
        await state.clear()

    async def update(self, markup: TextMarkup):
        self._current_markup = markup
        message_id = storage.get(f"{self.chat_id}")
        await self.state.set_state(markup.state)
        try:
            await bot.edit_message_text(
                chat_id=self.chat_id,
                message_id=message_id,
                text=(await markup.text) + ('\n' + self.feedback.text.as_html() if self.feedback.active else ''),
                reply_markup=await markup.markup
            )
        except TelegramBadRequest as e:
            info.warning(e)

        await self.feedback.reset()
        self.feedback.off()
        await self.clean_trash()
        await self.update_interface_in_redis()

    async def update_feedback(self, msg: str, type_: Literal["default", "info", "error"] = "default", active=True):
        self.feedback.header = self._feedback_headers[type_]
        self.feedback.data = msg
        if active:
            self.feedback.on()

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

    async def handling_unexpected_error(self, response):
        await self.update_feedback('internal server error', type_="error")
        await self._current_markup.open()

        try:
            response_ = await response.json()
            errors.error(
                f"Current markup: {self._current_markup.__class__.__name__}\nDetail: {response_['detail']}\nStatus: {response.status}"
            )
        except (ContentTypeError, Exception):
            errors.error("internal server error")

    async def encoded_chat_id(self):
        return await encode_jwt({'telegram_id': self.chat_id})

    async def notification_on(self):
        async with self.session.get(f'/notification_time/{await self.encoded_chat_id()}') as response:
            if response.status == 200:
                time_ = await response.json()
                scheduler.add_job(
                    func=remainder,
                    trigger=CronTrigger(hour=time_["hour"], minute=time_["minute"]),
                    args=(self.chat_id,), replace_existing=True, id=str(self.chat_id)
                )

    async def notification_off(self):
        try:
            scheduler.remove_job(job_id=self.chat_id, jobstore='default')
        except JobLookupError:
            pass
            # info.warning(f'With try to delete job, it was not found for user: {self.chat_id}')

    async def update_notification_time(self):
        hour = storage.get("hour")
        minute = storage.get("minute")
        try:
            scheduler.modify_job(self.chat_id, trigger=CronTrigger(hour=hour, minute=minute))
        except JobLookupError:
            pass

    async def update_interface_in_redis(self):
        state = self.state
        session = self.session
        self.state = None
        self.session = None
        await state.update_data({'interface': await self.serialize()})
        self.state = state
        self.session = session

    async def temp_message(self, msg="Processing..."):
        message_id = storage.get(f"{self.chat_id}")
        try:
            await bot.edit_message_text(text=msg, chat_id=self.chat_id, message_id=message_id)
        except TelegramBadRequest:
            pass

    async def _reset_state(self):
        await self.state.set_state(None)
        self.token = None



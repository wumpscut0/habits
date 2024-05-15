import os
from typing import Literal, Iterable

from aiogram.exceptions import TelegramBadRequest
from aiohttp import ContentTypeError
from apscheduler.jobstores.base import JobLookupError
from apscheduler.triggers.cron import CronTrigger
from cryptography.fernet import Fernet

from frontend.bot import bot
from frontend.markups.basic import BasicManager
from frontend.markups.core import TextMarkup, DataTextWidget
from frontend.markups.targets import TargetsManager
from frontend.utils import SerializableMixin, Emoji, storage
from frontend.utils.loggers import errors, info
from frontend.utils.scheduler import scheduler, remainder


class Interface(SerializableMixin):
    _feedback_headers = {
        "default": f'{Emoji.REPORT} Feedback',
        "info": f"{Emoji.INFO} Info",
        "error": f"{Emoji.DENIAL} Error"
    }
    _cipher = Fernet(os.getenv("CIPHER"))

    def __init__(self, chat_id: int):
        self.basic_manager = BasicManager(self)
        self.targets_manager = TargetsManager(self)

        self.chat_id = chat_id
        self.token = None
        self.feedback = DataTextWidget(active=False)

        self.state = None
        self.session = None

        self._current_markup = None

    async def open_session(self, close_msg='Session close'):
        await self.close_session(close_msg)
        await self.basic_manager.title_screen.open(new_session=True)

    async def close_session(self, close_msg="Session close"):
        await self._reset_state()
        message_id = storage.get(str(self.chat_id))
        try:
            message = await bot.edit_message_text(
                chat_id=self.chat_id,
                message_id=message_id,
                text=close_msg
            )
            await self.refill_trash(message.message_id)
        except TelegramBadRequest:
            pass

    async def clear(self):
        message_id = storage.get(f"{self.chat_id}")
        if self.chat_id is not None and message_id is not None:
            await bot.delete_message(chat_id=self.chat_id, message_id=message_id)
        await self.clean_trash()
        await self.state.clear()

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
        trash = storage.get(f"trash:{self.chat_id}")
        for message_id in trash:
            try:
                await bot.delete_message(self.chat_id, message_id)
            except TelegramBadRequest:
                try:
                    await bot.edit_message_text('deleted', self.chat_id, message_id)
                except TelegramBadRequest:
                    pass
        storage.delete(f"trash:{self.chat_id}")

    async def refill_trash(self, message_id: int):
        trash = storage.get(f"trash:{self.chat_id}")
        trash.append(message_id)
        storage.set(f"trash:{self.chat_id}")

    async def handling_unexpected_error(self, response):
        await self.update_feedback('internal server error', type_="error")
        await self._reset_state()
        await self.clean_trash()
        await self.basic_manager.title_screen.open()

        try:
            response_ = await response.json()
            errors.error(
                f"Current markup: {self._current_markup.__class__.__name__}\nDetail: {response_['detail']}\nStatus: {response.status}"
            )
        except (ContentTypeError, Exception):
            errors.error("internal server error")

    async def refresh_notifications(self):
        user_response = await self.get_user()
        targets_response = await self.get_targets()
        if user_response is not None and targets_response is not None:
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
                    args=(self.chat_id,), replace_existing=True, id=str(self.chat_id)
                )
            else:
                try:
                    scheduler.remove_job(job_id=self.chat_id, jobstore='default')
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

    async def get_user(self):
        async with self.session.get(
                f'/users/{self._cipher.encrypt(bytes(self.chat_id))}',
                headers={"Authorization": storage.get("service_key")}
        ) as response:
            return await self.response_middleware(response)

    async def get_targets(self):
        async with self.session.get(
                f'/targets',
                headers={"Authorization": self.token}
        ) as response:
            return await self.response_middleware(response)

    async def response_middleware(self, response, *args: int):
        """
        :param args: is expected response codes
        :return: None if response code not in args
        """
        if response.status in args:
            return response
        elif response.status == 401:
            await self.close_session()
        else:
            await self.handling_unexpected_error(response)

    async def _reset_state(self):
        await self.state.set_state(None)
        self.token = None





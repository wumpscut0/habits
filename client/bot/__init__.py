import os

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiohttp import ContentTypeError

from client.api import ServerApi
from client.markups.basic import TitleScreen
from client.markups.core import DataTextWidget
from client.utils import Emoji
from client.utils.loggers import errors
from client.utils.redis import Storage

bot = Bot(os.getenv('TOKEN'), parse_mode='HTML')

class BotControl:
    _feedback_headers = {
        "default": f'{Emoji.REPORT} Feedback',
        "info": f"{Emoji.INFO} Info",
        "error": f"{Emoji.DENIAL} Error"
    }

    def __init__(self, chat_id: int):
        super().__init__(self, chat_id)
        self.storage = Storage(chat_id)
        self.server = ServerApi(self)

        self.chat_id = chat_id
        self.feedback = DataTextWidget(active=False)

        self.state = None

    async def clean_trash(self):
        for message_id in self.storage.trash:
            await self.delete_message(message_id)

    async def refill_trash(self, message_id: int):
        trash = self.storage.trash
        trash.append(message_id)
        self.storage.trash = trash

    async def delete_message(self, message_id):
        try:
            await bot.delete_message(self.chat_id, message_id)
        except TelegramBadRequest:
            try:
                await bot.edit_message_text('deleted', self.chat_id, message_id)
            except TelegramBadRequest:
                pass

    async def open_session(self, close_msg='Session close'):
        message_id = await self.close_session(close_msg)
        await TitleScreen().open(new_session=True)
        if message_id is not None:
            await self.refill_trash(message_id)

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
        except TelegramBadRequest:
            pass

        self.feedback.off()
        await self.clean_trash()
        await self.update_interface_in_redis()

    async def update_feedback(self, msg: str, type_: Literal["default", "info", "error"] = "default", active=True):
        self.feedback.header = self._feedback_headers[type_]
        self.feedback.data = msg
        if active:
            self.feedback.on()



    async def handling_unexpected_error(self, response):
        await self.update_feedback('internal server error', type_="error")
        await self.open_session()

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
        self.state = None
        await state.update_data({'interface': await self.serialize()})
        self.state = state

    async def temp_message(self, msg="Processing..."):
        message_id = storage.get(f"{self.chat_id}")
        try:
            await bot.edit_message_text(text=msg, chat_id=self.chat_id, message_id=message_id)
        except TelegramBadRequest:
            pass

    async def clean_trash(self):
        trash =
        for message_id in self._interface.storage.trash:
            await self.delete_message(message_id)
        storage.delete(f"trash:{self.chat_id}")

    async def close_session(self, close_msg="Session close"):
        await self.clean_trash()
        await self.state.set_state(None)
        storage.delete(f"token:{self.chat_id}")
        message_id = storage.get(str(self.chat_id))
        try:
            message = await bot.edit_message_text(
                chat_id=self.chat_id,
                message_id=message_id,
                text=close_msg
            )
            return message.message_id
        except TelegramBadRequest:
            pass

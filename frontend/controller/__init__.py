from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiohttp import ClientSession
from aiohttp.web_response import Response
from apscheduler.triggers.cron import CronTrigger

from frontend.bot import bot
from frontend.markups.basic import BasicManager
from frontend.markups.core import TextMarkup, DataTextWidget
from frontend.markups.targets import TargetsManager
from frontend.utils import SerializableMixin, Emoji, encode_jwt
from frontend.utils.loggers import errors, info
from frontend.utils.scheduler import scheduler, remainder


class Interface(SerializableMixin):
    def __init__(self, chat_id: int, first_name: str):
        self.basic_manager = BasicManager(self)
        self.targets_manager = TargetsManager(self)

        self.first_name = first_name
        self.chat_id = chat_id
        self.token = None
        self.feedback = DataTextWidget(header=f'{Emoji.REPORT} Feedback', active=False)
        self.storage = {}

        self._message_id = None
        self._current_markup = None
        self._trash = []

    async def open_session(self, state, session: ClientSession, close_msg='Session close'):
        await self._reset_state(state)

        try:
            message = await bot.edit_message_text(
                chat_id=self.chat_id,
                message_id=self._message_id,
                text=close_msg
            )
            self._trash.append(message.message_id)
        except TelegramBadRequest:
            pass

        async with session.get(f'/notification_is_on/{await encode_jwt({"telegram_id": self.chat_id})}') as response:
            response_ = await response.text()
            if response_ == '1':
                self.basic_manager.title_screen.markup_map["notifications"].mark = Emoji.BELL
            elif response_ == '0':
                self.basic_manager.title_screen.markup_map["notifications"].mark = Emoji.NOT_BELL
            else:
                errors.error(f'Unsuccessfully check notification, return code: {response.status}')

        message = await bot.send_message(
            chat_id=self.chat_id,
            text=await self.basic_manager.title_screen.text,
            reply_markup=await self.basic_manager.title_screen.markup
        )
        self._message_id = message.message_id

        await self._update_interface_in_redis(state)

    async def close_session(self, state):
        await self._reset_state(state)
        await self.basic_manager.title_screen.open(state)

    async def clear(self, state):
        await bot.delete_message(chat_id=self.chat_id, message_id=self._message_id)
        await self.clean_trash()
        await state.clear()

    async def update(self, state: FSMContext, markup: TextMarkup):
        self._current_markup = markup
        await state.set_state(markup.state)
        feedback = '\n' + self.feedback.text.as_html() if self.feedback.text is not None else ''
        try:
            await bot.edit_message_text(
                chat_id=self.chat_id,
                message_id=self._message_id,
                text=(await markup.text) + feedback,
                reply_markup=await markup.markup
            )
        except TelegramBadRequest as e:
            info.warning(e)

        await self.feedback.reset()
        self.feedback.off()
        await self.clean_trash()
        await self._update_interface_in_redis(state)

    async def update_feedback(self, feedback: str, active=True):
        self.feedback.data = feedback
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

    async def handling_unexpected_error(self, state, response):
        response = await response.json()
        self.feedback.data = 'internal server error'
        errors.error(f"Current markup: {self._current_markup.__class__.__name__}\nDetail: {response['detail']}\nStatus: {response.status}")
        await self._current_markup.open(state)

    async def user_encode_id(self):
        await encode_jwt({'telegram_id': self.chat_id})

    async def notification_on(self, session: ClientSession):
        async with

        scheduler.add_job(func=remainder, trigger=CronTrigger(hour=hour, minute=minute),
                          args=(self._interface.chat_id,), replace_existing=True, id=self._interface.chat_id)

    async def _reset_state(self, state: FSMContext):
        await state.set_state(None)
        self.token = None

    async def _update_interface_in_redis(self, state):
        await state.update_data({'interface': await self.serialize()})

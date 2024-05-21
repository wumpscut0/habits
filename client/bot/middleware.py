from typing import Any, Dict, Callable, Awaitable

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import Update

from client.bot import BotControl
from client.markups import Info
from client.utils import Emoji
from client.utils.loggers import errors


class BuildBotControl(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        bot_control = await self._build_bot_control(event, data["state"])
        data["bot_control"] = bot_control
        try:
            return await handler(event, data)
        except BaseException as e:
            errors.critical(f"An error occurred when execution some handler:\n{e}")
            await bot_control.update_text_message(
                Info(f"Something went wrong {Emoji.CRYING_CAT}\n"
                     f"You can write feedback by sending any message to the chat room."),
                )
            raise e

    @classmethod
    async def _build_bot_control(cls, event, state: FSMContext):
        user_id = await cls._extract_user_id(event)
        bot_control = BotControl(user_id, state)
        bot_control.storage.first_name = await cls._extract_first_name(event)
        return bot_control

    @classmethod
    async def _extract_user_id(cls, event: Update):
        try:
            user_id = event.message.chat.id
        except AttributeError:
            user_id = event.callback_query.message.chat.id
        return user_id

    @classmethod
    async def _extract_first_name(cls, event: Update):
        await cls._extract_user_id(event)
        try:
            first_name = event.message.from_user.first_name
        except AttributeError:
            first_name = event.callback_query.from_user.first_name
        return first_name

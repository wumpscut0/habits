import os
from typing import Any, Dict, Callable, Awaitable

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import Update, TelegramObject
from aiohttp import ClientSession

from client.bot import BotControl, bot


class BuildInterfaceMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        data["bot_control"] = await self.build_context(await self._extract_user_id(event))
        return await handler(event, data)

    @classmethod
    async def build_context(cls, user_id):
        bot_control = BotControl(user_id, bot)
        if bot_control.storage.is_user_exists is None:
            response = await bot_control.server.add_user()
            if response.status == 201 or response.status == 409:
                bot_control.storage.is_user_exists = True
        return bot_control

    @classmethod
    async def _extract_user_id(cls, event: Update):
        try:
            user_id = event.message.chat.id
        except AttributeError:
            user_id = event.callback_query.message.chat.id
        return user_id

    @classmethod
    async def _up_to_date_first_name(cls, event: Update):
        await cls._extract_user_id(event)
        try:
            user_id = event.message.chat.id
            first_name = event.message.from_user.first_name
            await event.message.delete()
        except AttributeError:
            user_id = event.callback_query.message.chat.id
            first_name = event.callback_query.from_user.first_name
        storage.set(f"first_name:{user_id}", first_name)

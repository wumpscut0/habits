import os
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from aiohttp import ClientSession


class CommonMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        data['current_data'] = await data['state'].get_data()
        async with ClientSession(os.getenv('BACKEND')) as session:
            data['session'] = session
            return await handler(event, data)

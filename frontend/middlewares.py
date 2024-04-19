import os
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aiohttp import ClientSession

from config import COMMANDS
from frontend.interface.abyss import abyss
from frontend.markups.interface import Interface
from frontend.utils import deserialize


class CommonMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:

        current_data = await data['state'].get_data()

        interface = current_data.get('interface')
        if interface is None:
            current_data['interface'] = await Interface().serialize()
            interface = await deserialize(current_data['interface'])
        else:
            interface = await deserialize(interface)
        data['interface'] = interface

        trash = current_data.get('trash')
        if trash is None:
            current_data['trash'] = []
            trash = current_data['trash']
        data['trash'] = trash

        data['message_id'] = current_data.get('message_id')

        await data['state'].update_data(current_data)

        async with ClientSession(os.getenv('BACKEND')) as session:
            data['session'] = session
            if event.message is not None and event.message.text in COMMANDS:
                return await abyss(event.message, data['state'], data['message_id'], data['trash'])
            return await handler(event, data)

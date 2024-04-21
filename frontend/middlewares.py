import os
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from aiohttp import ClientSession
from frontend.markups.interface import Interface
from frontend.utils import deserialize


class CommonMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        async with ClientSession(os.getenv('BACKEND')) as session:
            data['session'] = session

            current_data = await data['state'].get_data()

            interface = current_data.get('interface')
            if interface is None:
                await session.post('/sign_up', json={'telegram_id': event.message.from_user.id})
                current_data['interface'] = await Interface(event.bot, event.message.chat.id, data['state']).serialize()
                interface = await deserialize(current_data['interface'])
            else:
                interface = await deserialize(interface)
            data['interface'] = interface

            interface.update_meta_data()

            await data['state'].update_data(current_data)

            return await handler(event, data)

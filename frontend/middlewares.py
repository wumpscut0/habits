import os
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from aiohttp import ClientSession

from frontend.main import scheduler
from frontend.markups.interface import Interface
from frontend.markups.remainder import remainder
from frontend.utils import deserialize


class CommonMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        # await data['state'].clear()
        current_data = await data['state'].get_data()
        interface = current_data.get('interface')

        if interface is not None:
            session_context = ClientSession(os.getenv('BACKEND'), headers={"Authentication": interface.token})
        else:
            session_context = ClientSession(os.getenv('BACKEND'))

        async with session_context as session:
            data['session'] = session
            if interface is None:
                await session.post('/sign_up', json={'telegram_id': event.message.from_user.id})

                current_data['interface'] = await Interface(event.message.chat.id, event.message.from_user.first_name).serialize()
                scheduler.add_job(func=remainder, args=(event.message.chat.id,), replace_existing=True)
                interface = await deserialize(current_data['interface'])
            else:
                if event.message is not None:
                    first_name = event.message.from_user.first_name
                else:
                    first_name = event.callback_query.message.from_user.first_name
                interface = await deserialize(interface)
                interface.first_name = first_name
                current_data['interface'] = interface.serialize()

            data['interface'] = interface

            await data['state'].update_data(current_data)

            return await handler(event, data)

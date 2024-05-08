import os
from typing import Any, Dict, Callable, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Update, TelegramObject
from aiohttp import ClientSession

from frontend.controller import Interface
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
            interface = await deserialize(interface)

            session_context = ClientSession(
                os.getenv('BACKEND'),
                headers={"Authentication": interface.token if interface.token is not None else "None"}
            )
        else:
            session_context = ClientSession(
                os.getenv('BACKEND'),
                headers={"Authentication": "None"}
            )

        async with session_context as session:
            data['session'] = session
            if interface is None:
                user_id = event.message.from_user.id

                await session.post('/sign_up', json={'telegram_id': user_id})

                current_data['interface'] = Interface(user_id, event.message.from_user.first_name)
            else:
                if event.message is not None:
                    first_name = event.message.from_user.first_name
                    interface.first_name = first_name

                current_data['interface'] = interface

            data['interface'] = current_data['interface']
            current_data['interface'] = await current_data['interface'].serialize()
            await data['state'].update_data(current_data)

            return await handler(event, data)

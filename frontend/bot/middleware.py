import os
from typing import Any, Dict, Callable, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Update, TelegramObject
from aiohttp import ClientSession

from frontend.controller import Interface
from frontend.utils import deserialize
from frontend.utils.loggers import errors


class CommonMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        current_data = await data['state'].get_data()
        interface = current_data.get('interface')

        if interface is not None:
            try:
                interface = await deserialize(interface)
                headers = {"Authorization": interface.token if interface.token is not None else "None"}
            except (AttributeError, Exception):
                headers = {"Authorization": "None"}
                await data['state'].clear()
                interface = None

        else:
            headers = {"Authorization": "None"}

        session_context = ClientSession(
            os.getenv('BACKEND'),
            headers=headers
        )

        async with session_context as session:
            data['session'] = session
            if interface is None:
                try:
                    user_id = event.message.chat.id
                    first_name = event.message.from_user.first_name
                    await event.message.delete()
                except AttributeError:
                    user_id = event.callback_query.message.chat.id
                    first_name = event.callback_query.from_user.first_name

                await session.post('/sign_up', json={'telegram_id': user_id})

                interface = Interface(user_id, first_name)

                interface.state = data["state"]
                interface.session = session
                await interface.reset_session()

            else:
                if event.message is not None:
                    first_name = event.message.from_user.first_name
                    interface.first_name = first_name

                current_data['interface'] = interface

                data['interface'] = current_data['interface']
                current_data['interface'] = await current_data['interface'].serialize()
                await data['state'].update_data(current_data)

                interface.state = data["state"]
                interface.session = session
                return await handler(event, data)
                # try:
                #     return await handler(event, data)
                # except Exception as e:
                #     errors.critical(f"Last markup: {interface._current_markup.__class__.__name__} | {e}")
                #     try:
                #         user_id = event.message.chat.id
                #         first_name = event.message.from_user.first_name
                #         await event.message.delete()
                #     except AttributeError:
                #         user_id = event.callback_query.message.chat.id
                #         first_name = event.callback_query.from_user.first_name
                #
                #     await session.post('/sign_up', json={'telegram_id': user_id})
                #
                #     interface = Interface(user_id, first_name)
                #     await interface.update_feedback('internal server error', type_="error")
                #     interface.state = data["state"]
                #     interface.session = session
                #     await interface.reset_session()

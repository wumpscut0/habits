import os
from typing import Any, Dict, Callable, Awaitable

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import Update, TelegramObject
from aiohttp import ClientSession

from frontend.controller import Interface
from frontend.utils import storage


class BuildInterfaceMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        await self.build_interface(data["state"], await self._extract_user_id(event))
        return await handler(event, data)

    @classmethod
    async def build_interface(cls, state: FSMContext, user_id):
        async with ClientSession(os.getenv("BACKEND")) as session:
            interface = (await state.get_data()).get("interface")
            if interface is None:
                interface = Interface(user_id)
                token = storage.get("service_key")
                async with session.post('/users', json={'user_id': user_id},
                                        headers={"Authorization": token}) as response:
                    response = interface.response_middleware(response, 201, 409)
                    if response is not None:
                        interface.session = session
                        interface.state = state
                        await state.update_data({"interface": interface.serialize()})
                        return interface
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

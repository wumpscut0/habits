import os

from aiogram import Dispatcher, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.redis import RedisStorage, Redis
from aiogram.types import CallbackQuery
from aiohttp import ClientSession

from frontend.bot.middleware import CommonMiddleware
from frontend.controller import Interface
from frontend.routers.abyss import abyss_router
from frontend.routers.basic import basic_router
from frontend.routers.targets import targets_router


callback_abyss_router = Router()


@callback_abyss_router.callback_query()
async def callback_abyss(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    async with ClientSession(os.getenv('BACKEND')) as session:
        interface = Interface(callback.message.chat.id, callback.from_user.first_name)
        interface.state = state
        interface.session = session
        await interface.update_feedback("Application was updated. Please, sign in again.", type_="info")
        await interface.basic_manager.title_screen.open()


dispatcher = Dispatcher(storage=RedisStorage(Redis()))
dispatcher.update.middleware(CommonMiddleware())
dispatcher.include_routers(
    abyss_router,
    basic_router,
    targets_router,
    callback_abyss_router,
)



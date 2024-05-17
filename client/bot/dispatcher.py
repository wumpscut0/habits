import os

from aiogram import Dispatcher, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.redis import RedisStorage, Redis
from aiogram.types import CallbackQuery

from client.bot.middleware import BuildInterfaceMiddleware
from client.routers.abyss import abyss_router
from client.routers.basic import basic_router
from client.routers.targets import targets_router


callback_abyss_router = Router()


@callback_abyss_router.callback_query()
async def callback_abyss(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    interface = await BuildInterfaceMiddleware.build_context(state, callback.from_user.id)
    await interface.update_feedback("Something wrong. Try sign in again.", type_="info")
    await interface.basic_manager.title_screen.open()


dispatcher = Dispatcher(storage=RedisStorage(Redis(host=os.getenv("REDIS_HOST"), port=int(os.getenv("REDIS_PORT")))))
dispatcher.update.middleware(BuildInterfaceMiddleware)
dispatcher.include_routers(
    abyss_router,
    basic_router,
    targets_router,
    callback_abyss_router,
)



from aiogram import Dispatcher
from aiogram.fsm.storage.redis import RedisStorage, Redis

from frontend.bot.middleware import CommonMiddleware
from frontend.routers.abyss import abyss_router
from frontend.routers.basic import basic_router
from frontend.routers.targets import targets_router

dispatcher = Dispatcher(storage=RedisStorage(Redis()))
dispatcher.update.middleware(CommonMiddleware())
dispatcher.include_routers(
    abyss_router,
    basic_router,
    targets_router,
)

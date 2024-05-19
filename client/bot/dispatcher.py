import os

from aiogram import Dispatcher, Router
from aiogram.fsm.storage.redis import RedisStorage, Redis
from aiogram.types import CallbackQuery, Message

from client.bot import BotControl
from client.bot.middleware import BuildBotControl
from client.handlers.abyss import abyss_router
from client.handlers.commands import commands_router
from client.markups.basic import TitleScreen
from client.handlers.basic import basic_router
from client.handlers.targets import targets_router


dispatcher = Dispatcher(storage=RedisStorage(Redis(host=os.getenv("REDIS_HOST"), port=int(os.getenv("REDIS_PORT")))))
dispatcher.update.middleware(BuildBotControl())
dispatcher.include_routers(
    commands_router,
    basic_router,
    targets_router,
    abyss_router,
)



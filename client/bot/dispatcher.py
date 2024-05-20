import os

from aiogram import Dispatcher, Router
from aiogram.fsm.storage.redis import RedisStorage, Redis
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Filter

from client.bot import BotControl
from client.bot.middleware import BuildBotControl
from client.handlers.abyss import abyss_router
from client.handlers.commands import commands_router
from client.handlers.profile import profile_router
from client.handlers.basic import basic_router
from client.handlers.targets import targets_router


class MessagePrivateFilter:
    def __call__(self, message: Message):
        return message.chat.type == "private"


class CallbackPrivateFilter:
    def __call__(self, callback: CallbackQuery):
        return callback.message.chat.type == "private"


dispatcher = Dispatcher(storage=RedisStorage(Redis(host=os.getenv("REDIS_HOST"), port=int(os.getenv("REDIS_PORT")))))
dispatcher.update.middleware(BuildBotControl())
dispatcher.message.filter(MessagePrivateFilter())
dispatcher.callback_query.filter(CallbackPrivateFilter())
dispatcher.include_routers(
    commands_router,
    basic_router,
    profile_router,
    targets_router,
    abyss_router,
)



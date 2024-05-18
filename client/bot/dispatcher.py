import os

from aiogram import Dispatcher, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.redis import RedisStorage, Redis
from aiogram.types import CallbackQuery

from client.bot import BotControl
from client.bot.middleware import BuildBotControl
from client.markups.basic import TitleScreen
from client.handlers.abyss import abyss_router
from client.handlers.basic import basic_router
from client.handlers.targets import targets_router


callback_abyss_router = Router()


@callback_abyss_router.callback_query()
async def callback_abyss(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.update_interface(await TitleScreen().init(str(bot_control.user_id)))


dispatcher = Dispatcher(storage=RedisStorage(Redis(host=os.getenv("REDIS_HOST"), port=int(os.getenv("REDIS_PORT")))))
dispatcher.update.middleware(BuildBotControl)
dispatcher.include_routers(
    abyss_router,
    basic_router,
    targets_router,
    callback_abyss_router,
)



from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message

from client.bot import BotControl
from client.bot.FSM import States
from client.markups import Input, Info
from client.utils import Emoji, config

common_router = Router()


@common_router.callback_query(F.data == "return_to_context")
async def return_to_context(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.return_to_context()

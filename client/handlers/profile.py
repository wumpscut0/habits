from aiogram import Router, F
from aiogram.types import CallbackQuery

from client.bot import BotControl
from client.bot.FSM import States
from client.markups import Input, Info

from client.markups.specific import Options, TitleScreen, Profile
from client.utils import Emoji

profile_router = Router()


@profile_router.callback_query(F.data == "title_screen")
async def title_screen(callback: CallbackQuery, bot_control: BotControl):
    bot_control.set_context(TitleScreen, bot_control.user_id)
    await bot_control.update_text_message(await TitleScreen(bot_control.user_id).init())


@profile_router.callback_query(F.data == "profile")
async def profile(callback: CallbackQuery, bot_control: BotControl):
    bot_control.set_context(Profile, bot_control.storage.first_name)
    await bot_control.update_text_message(Profile(bot_control.storage.first_name))


@profile_router.callback_query(F.data == "options")
async def options(callback: CallbackQuery, bot_control: BotControl):
    bot_control.set_context(Options, bot_control.user_id)
    await bot_control.update_text_message(await Options(bot_control.user_id).init())

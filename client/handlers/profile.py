from aiogram import Router, F
from aiogram.types import CallbackQuery

from client.bot import BotControl
from client.bot.FSM import States
from client.markups import Input

from client.markups.specific import Options, TitleScreen, Profile
from client.utils import Emoji

profile_router = Router()


@profile_router.callback_query(F.data == "title_screen")
async def title_screen(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.update_text_message(await TitleScreen().init(bot_control.user_id))


@profile_router.callback_query(F.data == "profile")
async def profile(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.update_text_message(Profile(bot_control.storage.first_name))


@profile_router.callback_query(F.data == "options")
async def options(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.update_text_message(await Options().init(bot_control.user_id))


@profile_router.callback_query(F.data == "input_password")
async def options(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.update_text_message(Input(
        f"{Emoji.KEY}{Emoji.NEW} Input new password",
        state=States.input_password
    ), context=False)

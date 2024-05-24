from aiogram import Router, F
from aiogram.types import CallbackQuery

from client.bot import BotControl

from client.markups.specific import Options, TitleScreen, Profile

profile_router = Router()


@profile_router.callback_query(F.data == "profile")
async def profile(callback: CallbackQuery, bot_control: BotControl):
    bot_control.set_context(
        Profile, bot_control.storage.user_token, bot_control.storage.first_name
    )
    await bot_control.update_text_message(
        await Profile(
            bot_control.storage.user_token, bot_control.storage.first_name
        ).init()
    )


@profile_router.callback_query(F.data == "options")
async def options(callback: CallbackQuery, bot_control: BotControl):
    bot_control.set_context(Options, bot_control.user_id)
    await bot_control.update_text_message(await Options(bot_control.user_id).init())


@profile_router.callback_query(F.data == "title_screen")
async def title_screen(callback: CallbackQuery, bot_control: BotControl):
    bot_control.set_context(TitleScreen, bot_control.user_id)
    await bot_control.update_text_message(await TitleScreen(bot_control.user_id).init())

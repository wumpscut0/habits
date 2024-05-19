from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

from client.bot import BotControl
from client.markups import TextMessageMarkup, TextWidget, ButtonWidget
from client.markups.basic import TitleScreen, Info, Conform

abyss_router = Router()


@abyss_router.callback_query(F.data == "close_info")
async def close_info(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.refresh_context()


@abyss_router.callback_query()
async def callback_abyss(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.update_text_message(await Info("Sorry. This button no working so far.").init(), context=False)


@abyss_router.message()
async def abyss(message: Message, bot_control: BotControl):
    await bot_control.update_text_message(await Conform(
        "Do you want to send message your psychotherapist?",
        "abyss_yes",
        "abyss_no"
    ).init())
    await message.delete()


@abyss_router.callback_query(F.data == "abyss_yes")
async def deep_abyss(message: Message, bot_control: BotControl):
    await bot_control.update_text_message(Te)
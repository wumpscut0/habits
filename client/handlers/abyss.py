from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message

from client.bot import BotControl
from client.bot.FSM import States
from client.markups import Input, Info, Conform
from client.utils import Emoji

abyss_router = Router()


@abyss_router.callback_query(F.data == "return_to_context")
async def return_to_context(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.return_to_context()


@abyss_router.callback_query(F.data == "abyss_yes")
async def abyss_yes(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.update_text_message(Input(
        F"Enter your message {Emoji.REPORT}",
        state=States.abyss_input
    ).text_message_markup, context=False)


@abyss_router.message(StateFilter(States.abyss_input), F.text)
async def abyss_yes_accept_input(message: Message, bot_control: BotControl):
    await bot_control.send_message_to_admin(message.text)
    await message.delete()
    await bot_control.update_text_message(Info(
        f"Message sent {Emoji.INCOMING_ENVELOPE}"
    ).text_message_markup, context=False)


@abyss_router.callback_query()
async def callback_abyss(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.update_text_message(Info(
        f"Sorry. This button no working so far. {Emoji.CRYING_CAT}\nTry /start"
    ).text_message_markup, context=False)


@abyss_router.message()
async def message_abyss(message: Message, bot_control: BotControl):
    await bot_control.update_text_message(Conform(
        f"Want to report a bug? {Emoji.BUG}\n"
        f"Or leave ideas on how to improve functionality? {Emoji.SHINE_STAR}",
        "abyss_yes",
    ).text_message_markup, context=False)
    await message.delete()

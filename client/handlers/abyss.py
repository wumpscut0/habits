from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from client.bot import BotControl
from client.markups import Info, Conform
from client.utils import Emoji

abyss_router = Router()


@abyss_router.callback_query()
async def callback_abyss(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.update_text_message(Info(
        f"Sorry. This button no working so far. {Emoji.CRYING_CAT}"
    ))


@abyss_router.message(~StateFilter(None))
async def wrong_type_message_abyss(message: Message, bot_control: BotControl, state: FSMContext):
    state_name = await state.get_state()

    guess = ""
    if "text" in state_name:
        guess = "text"
    elif "photo" in state_name:
        guess = "photo"

    if guess is not None:
        guess = f"Try to send {guess}"
    await bot_control.update_text_message(
        Info(f"Wrong message type {Emoji.BROKEN_HEARTH} {guess}")
    )
    await message.delete()


@abyss_router.message()
async def message_abyss(message: Message, bot_control: BotControl):
    await bot_control.update_text_message(Conform(
        f"Want to report a bug? {Emoji.BUG}\n"
        f"Or leave ideas on how to improve functionality? {Emoji.SHINE_STAR}",
        "send_message_to_admin",
    ))
    await message.delete()

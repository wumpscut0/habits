from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message

from client.bot import BotControl
from client.bot.FSM import States
from client.markups import Input, Info
from client.utils import Emoji, config

common_router = Router()

MAX_EMAIL_LENGTH = config.getint('limitations', 'MAX_EMAIL_LENGTH')
MAX_NAME_LENGTH = config.getint('limitations', 'MAX_NAME_LENGTH')
MAX_DESCRIPTION_LENGTH = config.getint('limitations', 'MAX_DESCRIPTION_LENGTH')
MAX_PASSWORD_LENGTH = config.getint('limitations', "MAX_PASSWORD_LENGTH")
MIN_BORDER_RANGE = config.getint('limitations', "MIN_BORDER_RANGE")
MAX_BORDER_RANGE = config.getint('limitations', "MAX_BORDER_RANGE")
STANDARD_BORDER_RANGE = config.getint('limitations', "STANDARD_BORDER_RANGE")
VERIFY_CODE_EXPIRATION = config.getint("limitations", "VERIFY_CODE_EXPIRATION")


@common_router.callback_query(F.data == "return_to_context")
async def return_to_context(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.return_to_context()


@common_router.callback_query(F.data == "send_message_to_admin")
async def send_message_to_admin(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.update_text_message(Input(
        f"Enter your message {Emoji.PENCIL}",
        state=States.input_text_to_admin
    ))


@common_router.message(StateFilter(States.input_text_to_admin), F.text)
async def send_message_to_admin_accept_input(message: Message, bot_control: BotControl):
    await bot_control.send_message_to_admin(message.text)
    await message.delete()
    await bot_control.update_text_message(Info(
        f"Message sent {Emoji.INCOMING_ENVELOPE}"
    ))

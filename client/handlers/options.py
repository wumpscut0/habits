import re

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message

from client.bot import BotControl
from client.bot.FSM import States
from client.handlers import MAX_EMAIL_LENGTH
from client.markups import Input, Info, Temp

from client.utils import Emoji
from client.utils.mailing import Mailing

options_router = Router()


@options_router.callback_query(F.data == "input_password")
async def input_password(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.update_text_message(Input(
        f"{Emoji.KEY + Emoji.NEW} Enter new password",
        state=States.input_text_password
    ))


@options_router.callback_query(F.data == "delete_password")
async def delete_password(callback: CallbackQuery, bot_control: BotControl):
    data, code = await bot_control.api.delete_password(bot_control.storage.user_token)
    if code == 200:
        await bot_control.update_text_message(Info(f"Password deleted {Emoji.KEY + Emoji.DENIAL}"))
        return

    await callback.answer("Internal server error")


@options_router.callback_query(F.data == "input_email")
async def input_email(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.update_text_message(Input(
        f"{Emoji.KEY + Emoji.NEW} Input new email {Emoji.ENVELOPE}",
        state=States.input_text_email
    ))


@options_router.message(StateFilter(States.input_text_email), F.text)
async def email_accept_input(message: Message, bot_control: BotControl):
    email = message.text
    await message.delete()

    if len(email) > MAX_EMAIL_LENGTH:
        await bot_control.update_text_message(
            Input(
                f'Max email length is {MAX_EMAIL_LENGTH} symbols. Try again. {Emoji.ENVELOPE}',
                state=States.input_text_email
            )
        )
    elif not re.fullmatch(r'[a-zA-Z0-9]+@[a-zA-Z]+\.[a-zA-Z]', email, flags=re.I):
        await bot_control.update_text_message(
            Input(
                f'Allowable format is "example@email.com". Try again. {Emoji.ENVELOPE}',
                state=States.input_text_email
            )
        )
    else:
        await bot_control.update_text_message(
            Temp()
        )
        verify_code = await Mailing.verify_email(email)
        if verify_code is not None:
            await bot_control.update_text_message(Input(
                f"Verify code sent on email: {email} {Emoji.ENVELOPE}"
            ))
            bot_control.storage.verify_code = verify_code
            bot_control.storage.email = email
        else:
            await bot_control.update_text_message(
                Input(
                    f'Email not found. Try again. {Emoji.ENVELOPE}',
                    state=States.input_text_email
                )
            )

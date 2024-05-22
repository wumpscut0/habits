from passlib.hash import pbkdf2_sha256
from aiogram.types import CallbackQuery
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message

from client.bot import BotControl
from client.bot.FSM import States
from client.markups import Input, Info, Temp
from client.markups.specific import TitleScreen, AuthenticationWithPassword, Profile, PasswordResume
from client.utils import Emoji, config
from client.utils.mailing import Mailing

MAX_EMAIL_LENGTH = config.getint('limitations', 'MAX_EMAIL_LENGTH')
MAX_NAME_LENGTH = config.getint('limitations', 'MAX_NAME_LENGTH')
MAX_DESCRIPTION_LENGTH = config.getint('limitations', 'MAX_DESCRIPTION_LENGTH')
MAX_PASSWORD_LENGTH = config.getint('limitations', "MAX_PASSWORD_LENGTH")
MIN_BORDER_RANGE = config.getint('limitations', "MIN_BORDER_RANGE")
MAX_BORDER_RANGE = config.getint('limitations', "MAX_BORDER_RANGE")
STANDARD_BORDER_RANGE = config.getint('limitations', "STANDARD_BORDER_RANGE")
VERIFY_CODE_EXPIRATION = config.getint("limitations", "VERIFY_CODE_EXPIRATION")

basic_router = Router()


@basic_router.callback_query(F.data == 'invert_notifications')
async def invert_notifications(callback: CallbackQuery, bot_control: BotControl):
    _, code = await bot_control.api.invert_notifications(bot_control.user_id)
    if await bot_control.api_status_code_processing(code, 200):
        data, code = await bot_control.api.get_user(bot_control.user_id)
        if await bot_control.api_status_code_processing(code, 200):
            if data["notifications"]:
                await callback.answer("Notifications online")
            else:
                await callback.answer("Notifications offline")
            await bot_control.update_text_message(await TitleScreen(bot_control.user_id).init())


@basic_router.callback_query(F.data == 'authorization')
async def authorization(callback: CallbackQuery, bot_control: BotControl):
    data, code = await bot_control.api.get_user(bot_control.user_id)
    if await bot_control.api_status_code_processing(code, 200):
        if data["hash"]:
            await bot_control.update_text_message(await AuthenticationWithPassword(bot_control.user_id).init())
        else:
            data, code = await bot_control.api.authentication(bot_control.user_id)
            if await bot_control.api_status_code_processing(code, 200):
                bot_control.storage.user_token = data["access_token"]
                bot_control.set_context(Profile, bot_control.storage.first_name)
                await bot_control.update_text_message(Profile(bot_control.storage.first_name))


@basic_router.message(StateFilter(States.input_text_sign_in_with_password), F.text)
async def password_accept_input(message: Message, bot_control: BotControl):
    password = message.text
    await message.delete()

    data, code = await bot_control.api.authentication(bot_control.user_id, password)
    if await bot_control.api_status_code_processing(code, 200, 401):
        if code == 200:
            bot_control.storage.user_token = data["access_token"]
            bot_control.set_context(Profile, bot_control.storage.first_name)
            await bot_control.update_text_message(Profile(bot_control.storage.first_name))
        elif code == 401:
            await bot_control.update_text_message(await AuthenticationWithPassword(
                bot_control.user_id,
                f"Wrong password {Emoji.CRYING_CAT} Try Again {Emoji.KEY}"
            ).init())


@basic_router.callback_query(F.data == "reset_password")
async def reset_password(callback: CallbackQuery, bot_control: BotControl):
    data, code = await bot_control.api.get_user(bot_control.user_id)
    if await bot_control.api_status_code_processing(code, 200):
        email = data["email"]
        await bot_control.update_text_message(Temp())
        verify_code = await Mailing.verify_email(email)
        if verify_code is None:
            await bot_control.update_text_message(
                Info(
                    f'Failed to send email {Emoji.CRYING_CAT} Sorry',
                )
            )
            return

        bot_control.storage.email = email
        bot_control.storage.verify_code = verify_code
        await bot_control.update_text_message(Input(
            f'Verify code sent on your email {Emoji.INCOMING_ENVELOPE}',
            state=States.input_text_verify_code_reset_password
        ))


@basic_router.message(StateFilter(States.input_text_verify_code_reset_password), F.text)
async def verify_code_to_reset_password_accept_input(message: Message, bot_control: BotControl):
    input_verify_code = message.text
    await message.delete()

    verify_code = bot_control.storage.verify_code
    if verify_code is None:
        await bot_control.update_text_message(Temp())
        bot_control.storage.verify_code = await Mailing.verify_email(bot_control.storage.email)
        await bot_control.update_text_message(Input(
            f'Verify code expired {Emoji.HOURGLASS_END}'
            f' New code sent on your email {Emoji.INCOMING_ENVELOPE}',
            state=States.input_text_verify_code_reset_password
        ))
        return

    if input_verify_code != str(verify_code):
        await bot_control.update_text_message(Input(
            f'Wrong verify code {Emoji.CRYING_CAT} Try again',
            state=States.input_text_verify_code_reset_password
        ))
        return

    await bot_control.update_text_message(Input(
        f"{Emoji.KEY + Emoji.NEW} Enter new password",
        state=States.input_text_password
    ))


@basic_router.message(StateFilter(States.input_text_password), F.text)
async def new_password_accept_input(message: Message, bot_control: BotControl):
    password = message.text
    await message.delete()

    if len(password) > MAX_PASSWORD_LENGTH:
        await bot_control.update_text_message(Input(
            f'Maximum password length is {MAX_PASSWORD_LENGTH} symbols {Emoji.CRYING_CAT}'
            f' Try again {Emoji.KEY}',
            state=States.input_text_password
        ))
        return

    bot_control.storage.password = password
    await bot_control.update_text_message(Input(
        f"{Emoji.KEY}{Emoji.KEY} Repeat password",
        state=States.input_text_repeat_password
    ))


@basic_router.message(StateFilter(States.input_text_repeat_password), F.text)
async def repeat_password_accept_input(message: Message, bot_control: BotControl):
    repeat_password = message.text
    await message.delete()

    password = bot_control.storage.password
    if password is None:
        await bot_control.update_text_message(Input(
            f'Time for repeat password expired {Emoji.HOURGLASS_END} Try again {Emoji.KEY}',
        ))
        return

    if password != repeat_password:
        await bot_control.update_text_message(Input(
            f'Passwords not matched {Emoji.CRYING_CAT} Try again {Emoji.KEY}',
            state=States.input_text_password
        ))
        return

    bot_control.storage.hash = pbkdf2_sha256.hash(repeat_password)
    await bot_control.update_text_message(PasswordResume(repeat_password))


@basic_router.callback_query(F.data == "update_password")
async def update_password(callback: CallbackQuery, bot_control: BotControl):
    _, code = await bot_control.api.update_password(bot_control.user_id, bot_control.storage.hash)
    if await bot_control.api_status_code_processing(code, 200):
        bot_control.set_context(TitleScreen, bot_control.user_id)
        await bot_control.update_text_message(Info(
            f'Password updated {Emoji.KEY + Emoji.OK}'
        ))

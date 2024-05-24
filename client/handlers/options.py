import re

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message

from client.bot import BotControl
from client.bot.FSM import States

from client.markups import Input, Info, Temp
from client.markups.specific import ChangeNotificationsHour, NotificationsHourCallbackData, ChangeNotificationsMinute, \
    NotificationsMinuteCallbackData

from client.utils import Emoji, config
from client.utils.mailing import Mailing
from client.utils.scheduler import Scheduler

options_router = Router()


MAX_EMAIL_LENGTH = config.getint("limitations", "MAX_EMAIL_LENGTH")


@options_router.callback_query(F.data == "input_password")
async def input_password(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.update_text_message(Input(
        f"{Emoji.KEY + Emoji.NEW} Enter new password",
        state=States.input_text_password
    ))


@options_router.callback_query(F.data == "delete_password")
async def delete_password(callback: CallbackQuery, bot_control: BotControl):
    _, code = await bot_control.api.delete_password(bot_control.storage.user_token)
    if await bot_control.api_status_code_processing(code, 200):
        await bot_control.update_text_message(Info(f"Password deleted {Emoji.KEY + Emoji.DENIAL}"))


@options_router.callback_query(F.data == "input_email")
async def input_email(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.update_text_message(Input(
        f"{Emoji.EMAIL + Emoji.NEW} Enter new email",
        state=States.input_text_email
    ))


@options_router.message(StateFilter(States.input_text_email), F.text)
async def email_accept_input(message: Message, bot_control: BotControl):
    email = message.text
    await message.delete()

    if len(email) > MAX_EMAIL_LENGTH:
        await bot_control.update_text_message(
            Input(
                f'Max email length is {MAX_EMAIL_LENGTH} symbols {Emoji.CRYING_CAT} Try again {Emoji.EMAIL}',
                state=States.input_text_email
            )
        )
        return

    if not re.fullmatch(r'[a-zA-Z0-9]+@[a-zA-Z]+\.[a-zA-Z]+', email, flags=re.I):
        await bot_control.update_text_message(
            Input(
                f'Allowable format is "example123@gmail.com". Try again. {Emoji.EMAIL}',
                state=States.input_text_email
            )
        )
        return

    await bot_control.update_text_message(
        Temp()
    )
    verify_code = await Mailing.send_verify_code(
        email,
        "Verify email",
        bot_control.storage.first_name
    )

    if verify_code is None:
        await bot_control.update_text_message(
            Input(
                f'Email not found {Emoji.CRYING_CAT} Try again {Emoji.EMAIL}',
                state=States.input_text_email
            )
        )
        return

    await bot_control.update_text_message(Input(
        f"Verify code sent on email: {email} {Emoji.INCOMING_ENVELOPE}",
        state=States.input_text_verify_email_code
    ))
    bot_control.storage.verify_code = verify_code
    bot_control.storage.email = email


@options_router.message(StateFilter(States.input_text_verify_email_code), F.text)
async def email_accept_input(message: Message, bot_control: BotControl):
    input_verify_code = message.text
    await message.delete()

    verify_code = bot_control.storage.verify_code
    if verify_code is None:
        await bot_control.update_text_message(Temp())
        bot_control.storage.verify_code = await Mailing.send_verify_code(
            bot_control.storage.email,
            "Verify email",
            bot_control.storage.first_name
        )
        await bot_control.update_text_message(Input(
            f'Verify code expired {Emoji.HOURGLASS_END}'
            f' New code sent on email: {bot_control.storage.email} {Emoji.INCOMING_ENVELOPE}',
            state=States.input_text_verify_email_code
        ))
        return

    if input_verify_code != str(verify_code):
        await bot_control.update_text_message(Input(
            f'Wrong verify code {Emoji.CRYING_CAT} Try again',
            state=States.input_text_verify_email_code
        ))
        return

    _, code = await bot_control.api.update_email(bot_control.storage.user_token, bot_control.storage.email)
    if await bot_control.api_status_code_processing(code, 201):
        await bot_control.update_text_message(Info(
            f"Email updated {Emoji.EMAIL + Emoji.OK}"
        ))


@options_router.callback_query(F.data == "delete_email")
async def delete_email(callback: CallbackQuery, bot_control: BotControl):
    _, code = await bot_control.api.delete_email(bot_control.storage.user_token)
    if await bot_control.api_status_code_processing(code, 200):
        await bot_control.update_text_message(Info(f"Email deleted {Emoji.EMAIL + Emoji.DENIAL}"))


@options_router.callback_query(F.data == "change_notification_time")
async def change_notification_time(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.update_text_message(ChangeNotificationsHour())


@options_router.callback_query(NotificationsHourCallbackData.filter())
async def notifications_hour_accept_callback_data(
        callback: CallbackQuery,
        callback_data: NotificationsHourCallbackData,
        bot_control: BotControl
):
    bot_control.storage.hour = callback_data.hour
    await bot_control.update_text_message(ChangeNotificationsMinute())


@options_router.callback_query(NotificationsMinuteCallbackData.filter())
async def notifications_minute_accept_callback_data(
        callback: CallbackQuery,
        callback_data: NotificationsMinuteCallbackData,
        bot_control: BotControl
):
    _, code = await bot_control.api.update_notifications_time(
        bot_control.storage.user_token,
        bot_control.storage.hour,
        callback_data.minute,
    )
    if await bot_control.api_status_code_processing(code, 200):
        await Scheduler.refresh_notifications(bot_control.user_id)
        await bot_control.return_to_context()

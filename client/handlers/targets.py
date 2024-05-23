import re

from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message
from aiogram import Router, F

from client.bot import BotControl
from client.bot.FSM import States
from client.markups import Input, Conform, Info

from client.markups.specific import TargetsControl, CurrentTargetsListLeftCallbackData, CurrentTargetsList, \
    CurrentTargetsListRightCallbackData, CurrentTargetCallbackData, Target, InputBorder
from client.utils import config, Emoji
from client.utils.scheduler import Scheduler

targets_router = Router()

MAX_EMAIL_LENGTH = config.getint('limitations', 'MAX_EMAIL_LENGTH')
MAX_NAME_LENGTH = config.getint('limitations', 'MAX_NAME_LENGTH')
MAX_DESCRIPTION_LENGTH = config.getint('limitations', 'MAX_DESCRIPTION_LENGTH')
MIN_BORDER_RANGE = config.getint('limitations', "MIN_BORDER_RANGE")
MAX_BORDER_RANGE = config.getint('limitations', "MAX_BORDER_RANGE")
STANDARD_BORDER_RANGE = config.getint('limitations', "STANDARD_BORDER_RANGE")
VERIFY_CODE_EXPIRATION = config.getint("limitations", "VERIFY_CODE_EXPIRATION")

# Data size determine pagination rule.
# When does leaving the context become the context?
# Maybe add context autogenerate? How it`s done?


@targets_router.callback_query(F.data == "targets_control")
async def targets_control(callback: CallbackQuery, bot_control: BotControl):
    bot_control.set_context(TargetsControl, bot_control.storage.user_token)
    await bot_control.update_text_message(await TargetsControl(bot_control.storage.user_token).init())


@targets_router.callback_query(F.data == "current_targets")
async def current_targets(callback: CallbackQuery, bot_control: BotControl):
    bot_control.set_context(CurrentTargetsList, bot_control.storage.user_token)
    await bot_control.update_text_message(await CurrentTargetsList(bot_control.storage.user_token).init())


@targets_router.callback_query(CurrentTargetsListLeftCallbackData.filter())
async def current_targets_left(
        callback: CallbackQuery,
        callback_data: CurrentTargetsListLeftCallbackData,
        bot_control: BotControl
):
    bot_control.set_context(CurrentTargetsList, bot_control.storage.user_token, callback_data.page)
    await bot_control.update_text_message(await CurrentTargetsList(
        bot_control.storage.user_token,
        callback_data.page
    ).init())


@targets_router.callback_query(CurrentTargetsListRightCallbackData.filter())
async def current_targets_right(
        callback: CallbackQuery,
        callback_data: CurrentTargetsListRightCallbackData,
        bot_control: BotControl
):
    bot_control.set_context(CurrentTargetsList, bot_control.storage.user_token, callback_data.page)
    await bot_control.update_text_message(await CurrentTargetsList(
        bot_control.storage.user_token,
        callback_data.page
    ).init())


@targets_router.callback_query(CurrentTargetCallbackData.filter())
async def current_target(
        callback: CallbackQuery,
        callback_data: CurrentTargetCallbackData,
        bot_control: BotControl
):
    bot_control.storage.target_id = callback_data.id
    await bot_control.update_text_message(await Target(bot_control.storage.user_token, callback_data.id).init())


@targets_router.callback_query(CurrentTargetCallbackData.filter())
async def current_target(
        callback: CallbackQuery,
        callback_data: CurrentTargetCallbackData,
        bot_control: BotControl
):
    bot_control.storage.target_id = callback_data.id
    await bot_control.update_text_message(await Target(bot_control.storage.user_token, callback_data.id).init())


@targets_router.callback_query(F.data == "current_target")
async def current_target(
        callback: CallbackQuery,
        bot_control: BotControl
):
    await bot_control.update_text_message(await Target(bot_control.storage.user_token, bot_control.storage.target_id).init())


@targets_router.callback_query(F.data == "invert_completed")
async def invert_completed(callback: CallbackQuery, bot_control: BotControl):
    target_id = bot_control.storage.target_id
    token = bot_control.storage.user_token
    _, code = await bot_control.api.invert_completed(token, target_id)
    if await bot_control.api_status_code_processing(code, 200):
        await Scheduler.refresh_notifications(bot_control.user_id)
        await bot_control.update_text_message(await Target(token, target_id).init())


@targets_router.callback_query(F.data == "change_name")
async def change_name(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.update_text_message(Input(
        f"Enter new target name {Emoji.SPROUT}",
        back_callback_data="current_target",
        state=States.input_text_update_target_name
    ))


@targets_router.message(StateFilter(States.input_text_update_target_name))
async def input_text_update_target_name(message: Message, bot_control: BotControl):
    name = message.text
    await message.delete()

    if len(name) > MAX_NAME_LENGTH:
        await bot_control.update_text_message(Input(
            f"Maximum name length is {MAX_NAME_LENGTH} simbols {Emoji.CRYING_CAT} Try again",
            back_callback_data="current_target",
            state=States.input_text_update_target_name
        ))
        return

    if not re.fullmatch(r'[\w\s]+', name, flags=re.I):
        await bot_control.update_text_message(Input(
            f"Name must contains only latin symbols or _ or spaces or digits {Emoji.CRYING_CAT} Try again",
            back_callback_data="current_target",
            state=States.input_text_update_target_name
        ))
        return

    target_id = bot_control.storage.target_id
    token = bot_control.storage.user_token
    _, code = await bot_control.api.update_target(token, target_id, name=name)
    if await bot_control.api_status_code_processing(code, 200):
        await bot_control.update_text_message(await Target(token, target_id).init())


@targets_router.callback_query(F.data == "change_description")
async def change_description(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.update_text_message(Input(
        f"Enter new target description {Emoji.LIST_WITH_PENCIL}\n"
        f"Maximum description length is {MAX_DESCRIPTION_LENGTH} simbols\n"
        'Description must contains only latin symbols or "_,?!:.(" or spaces or digits\n',

        back_callback_data="current_target",
        state=States.input_text_update_target_description
    ))


@targets_router.message(StateFilter(States.input_text_update_target_description))
async def input_text_update_target_description(message: Message, bot_control: BotControl):
    description = message.text
    await message.delete()

    if len(description) > MAX_DESCRIPTION_LENGTH:
        await bot_control.update_text_message(Input(
            f"Maximum description length is {MAX_DESCRIPTION_LENGTH} simbols {Emoji.CRYING_CAT} Try again",
            back_callback_data="current_target",
            state=States.input_text_update_target_description
        ))
        return

    if not re.fullmatch(r'[\w\s,?!:.]+', description, flags=re.I):
        await bot_control.update_text_message(Input(
            f'Description must contains only latin symbols or "_,?!:." or spaces or digits {Emoji.CRYING_CAT} Try again',
            back_callback_data="current_target",
            state=States.input_text_update_target_description
        ))
        return

    target_id = bot_control.storage.target_id
    token = bot_control.storage.user_token
    _, code = await bot_control.api.update_target(token, target_id, description=description)
    if await bot_control.api_status_code_processing(code, 200):
        await bot_control.update_text_message(await Target(token, target_id).init())


@targets_router.callback_query(F.data == "delete_target")
async def delete_target(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.update_text_message(Conform(
        f"Do you really want to delete this target forever? {Emoji.WARNING}",
        "conform_delete_target",
        no_callback_data="current_target"
    ))
    await Scheduler.refresh_notifications(bot_control.user_id)


@targets_router.callback_query(F.data == "conform_delete_target")
async def conform_delete_target(callback: CallbackQuery, bot_control: BotControl):
    _, code = await bot_control.api.delete_target(bot_control.storage.user_token, bot_control.storage.target_id)
    if await bot_control.api_status_code_processing(code, 200):
        await bot_control.update_text_message(Info(
            f"Target deleted {Emoji.OK}"
        ))


@targets_router.callback_query(F.data == "create_target")
async def create_target(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.update_text_message(Input(
        f"Enter target name {Emoji.SPROUT}",
        state=States.input_text_target_name
    ))


@targets_router.message(StateFilter(States.input_text_target_name))
async def input_text_target_name(message: Message, bot_control: BotControl):
    name = message.text
    await message.delete()

    if len(name) > MAX_NAME_LENGTH:
        await bot_control.update_text_message(Input(
            f"Maximum name length is {MAX_NAME_LENGTH} simbols {Emoji.CRYING_CAT} Try again",
            state=States.input_text_target_name
        ))
        return

    if not re.fullmatch(r'[\w\s]+', name, flags=re.I):
        await bot_control.update_text_message(Input(
            f"Name must contains only latin symbols or _ or spaces or digits {Emoji.CRYING_CAT} Try again",
            state=States.input_text_target_name
        ))
        return

    bot_control.storage.target_name = name

    await bot_control.update_text_message(Input(
        f"Enter new target description {Emoji.LIST_WITH_PENCIL}\n"
        f"Maximum description length is {MAX_DESCRIPTION_LENGTH} simbols\n"
        'Description must contains only latin symbols or "_,?!:.(" or spaces or digits\n',
        state=States.input_text_target_description
    ))


@targets_router.message(StateFilter(States.input_text_target_description))
async def input_text_target_description(message: Message, bot_control: BotControl):
    description = message.text
    await message.delete()

    if len(description) > MAX_DESCRIPTION_LENGTH:
        await bot_control.update_text_message(Input(
            f"Maximum description length is {MAX_DESCRIPTION_LENGTH} simbols {Emoji.CRYING_CAT} Try again",
            back_callback_data="current_target",
            state=States.input_text_target_description
        ))
        return

    if not re.fullmatch(r'[\w\s,?!:.]+', description, flags=re.I):
        await bot_control.update_text_message(Input(
            f'Description must contains only latin symbols or "_,?!:." or spaces or digits {Emoji.CRYING_CAT} Try again',
            back_callback_data="current_target",
            state=States.input_text_target_description
        ))
        return

    bot_control.storage.target_description = description

    await bot_control.update_text_message(InputBorder())


@targets_router.message(StateFilter(States.input_text_target_border))
async def input_text_target_border(message: Message, bot_control: BotControl):
    border = message.text
    await message.delete()
    try:
        border = int(border)
    except ValueError:
        await bot_control.update_text_message(
            Input(f"Border value must be integer {Emoji.CRYING_CAT} Try again")
        )
        return

    if not MIN_BORDER_RANGE <= border <= MAX_BORDER_RANGE:
        await bot_control.update_text_message(Input(
            f'Border range must be at {MIN_BORDER_RANGE} to {MAX_BORDER_RANGE}',
            state=States.input_text_target_border
        ))
        return

    _, code = await bot_control.api.create_target(
        bot_control.storage.user_token,
        bot_control.storage.target_name,
        border,
        bot_control.storage.target_description,
    )
    if await bot_control.api_status_code_processing(code, 201):
        await Scheduler.refresh_notifications(bot_control.user_id)
        await bot_control.update_text_message(Info(
            f"Target created {Emoji.OK}"
        ))


@targets_router.callback_query(F.data == "conform_create_target")
async def conform_create_target(callback: CallbackQuery, bot_control: BotControl):
    _, code = await bot_control.api.create_target(
        bot_control.storage.user_token,
        bot_control.storage.target_name,
        STANDARD_BORDER_RANGE,
        bot_control.storage.target_description,
    )
    if await bot_control.api_status_code_processing(code, 201):
        await Scheduler.refresh_notifications(bot_control.user_id)
        await bot_control.update_text_message(Info(
            f"Target created {Emoji.OK}"
        ))

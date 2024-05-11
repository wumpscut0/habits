from aiohttp import ClientSession
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from frontend.markups.basic import NotificationMinuteCallbackData, NotificationHourCallbackData
from frontend.controller import Interface
from frontend.bot.FSM import States

basic_router = Router()


@basic_router.message(CommandStart())
async def open_tittle_screen(message: Message, interface: Interface):
    await interface.reset_session()
    await message.delete()


@basic_router.callback_query(F.data == 'title_screen')
async def open_tittle_screen(callback: CallbackQuery, interface: Interface):
    await interface.close_session()


@basic_router.callback_query(F.data == 'invert notifications')
async def invert_notifications(callback: CallbackQuery, interface: Interface):
    await interface.basic_manager.title_screen.invert_notifications()


@basic_router.callback_query(F.data == 'authorization')
async def authorization(callback: CallbackQuery, interface: Interface):
    await interface.basic_manager.title_screen.authorization()


@basic_router.message(StateFilter(States.sign_in_with_password), F.text)
async def authorization_with_password(message: Message, interface: Interface):
    await interface.basic_manager.authorization_with_password(message.text)
    await message.delete()


########################################################################################################################


@basic_router.callback_query(F.data == 'profile')
async def open_profile(callback: CallbackQuery, interface: Interface):
    await interface.basic_manager.profile.open()
    
    
########################################################################################################################


@basic_router.callback_query(F.data == "options")
async def open_options(callback: CallbackQuery, interface: Interface):
    await interface.basic_manager.options.open()
    

########################################################################################################################


@basic_router.callback_query(F.data == "update_password")
async def update_password(callback: CallbackQuery, interface: Interface):
    await interface.basic_manager.options.update_password()


@basic_router.callback_query(F.data == "reset_password")
async def reset_password(callback: CallbackQuery, interface: Interface):
    await interface.basic_manager.authorization_with_password.reset_password()


@basic_router.callback_query(F.data == "input_password")
async def open_input_password(callback: CallbackQuery, interface: Interface):
    await interface.basic_manager.input_password.open()


@basic_router.callback_query(F.data == "delete_password")
async def delete_password(callback: CallbackQuery, interface: Interface):
    await interface.basic_manager.options.delete_password()


@basic_router.message(StateFilter(States.input_password), F.text)
async def input_password(message: Message, interface: Interface):
    await interface.basic_manager.input_password(message.text)
    await message.delete()


@basic_router.message(StateFilter(States.repeat_password), F.text)
async def repeat_password(message: Message, interface: Interface):
    await interface.basic_manager.repeat_password(message.text)
    await message.delete()


@basic_router.message(StateFilter(States.input_verify_code_reset_password), F.text)
async def input_verify_code_reset_password(message: Message, interface: Interface):
    await interface.basic_manager.input_verify_code_reset_password(message.text)
    await message.delete()


########################################################################################################################


@basic_router.callback_query(F.data == 'input_email')
async def open_create_email(callback: CallbackQuery, interface: Interface):
    await interface.basic_manager.input_email.open()


@basic_router.callback_query(F.data == 'delete_email')
async def open_create_email(callback: CallbackQuery, interface: Interface):
    await interface.basic_manager.options.delete_email()


@basic_router.message(StateFilter(States.input_email), F.text)
async def input_email(message: Message, interface: Interface):
    await interface.basic_manager.input_email(message.text)
    await message.delete()


@basic_router.message(StateFilter(States.input_verify_email_code), F.text)
async def input_verify_email_code(message: Message, interface: Interface):
    await interface.basic_manager.input_verify_email_code(message.text)
    await message.delete()


########################################################################################################################


@basic_router.callback_query(F.data == "change_notification_time")
async def open_change_notification_time(callback: CallbackQuery, interface: Interface):
    await interface.basic_manager.change_notification_hour.open()


@basic_router.callback_query(NotificationHourCallbackData.filter())
async def change_notification_time(callback: CallbackQuery, callback_data: NotificationHourCallbackData, interface: Interface):
    await interface.basic_manager.change_notification_hour(callback_data.hour)


@basic_router.callback_query(NotificationMinuteCallbackData.filter())
async def change_notification_time(callback: CallbackQuery, callback_data: NotificationMinuteCallbackData, interface: Interface):
    await interface.basic_manager.change_notification_minute(callback_data.minute)

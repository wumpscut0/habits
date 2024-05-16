from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message

from client.markups.basic import NotificationMinuteCallbackData, NotificationHourCallbackData
from client.controller import Interface
from client.bot.FSM import States

basic_router = Router()


@basic_router.message(CommandStart())
async def open_tittle_screen(message: Message, interface: Interface):
    await self.clean_trash()
    await self.state.set_state(None)
    storage.delete(f"token:{self.chat_id}")
    message_id = storage.get(str(self.chat_id))
    try:
        message = await bot.edit_message_text(
            chat_id=self.chat_id,
            message_id=message_id,
            text=close_msg
        )
        return message.message_id
    except TelegramBadRequest:
        pass
    interface.storage.message_id
    message_id = await self.close_session(close_msg)
    await self.basic_manager.title_screen.open(new_session=True)
    if message_id is not None:
        await self.refill_trash(message_id)
    await interface.open_session()
    await message.delete()


@basic_router.callback_query(F.data == 'title_screen')
async def open_tittle_screen(callback: CallbackQuery, interface: Interface):
    await interface.basic_manager.title_screen.open()


@basic_router.callback_query(F.data == 'invert_notifications')
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


@basic_router.callback_query(F.data == "close_notification")
async def close_notification(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        await callback.message.edit_text("Deleted")
from frontend.markups.basic import NotificationHourCallbackData, NotificationMinuteCallbackData
from frontend.routers import *


basic_router = Router()


@basic_router.message(CommandStart())
async def open_tittle_screen(message: Message, interface: Interface, state: FSMContext):
    await interface.open_session(state)
    await message.delete()


@basic_router.callback_query(F.data == 'title_screen')
async def open_tittle_screen(callback: CallbackQuery, interface: Interface, state: FSMContext):
    await interface.close_session(state)


@basic_router.callback_query(F.data == 'invert_notifications')
async def invert_notifications(callback: CallbackQuery, interface: Interface, state: FSMContext, session: ClientSession):
    await interface.basic_manager.title_screen.invert_notifications(session, state)


@basic_router.callback_query(F.data == 'authorization')
async def authorization(callback: CallbackQuery, interface: Interface, state: FSMContext, session: ClientSession):
    await interface.basic_manager.title_screen.authorization(session, state)


########################################################################################################################


@basic_router.callback_query(F.data == 'profile')
async def open_profile(callback: CallbackQuery, interface: Interface, state: FSMContext):
    await interface.basic_manager.profile.open(state)
    
    
########################################################################################################################


@basic_router.callback_query(F.data == "options")
async def open_options(callback: CallbackQuery, interface: Interface, state: FSMContext):
    await interface.basic_manager.options.open(state)
    

########################################################################################################################


@basic_router.callback_query(F.data == "update_password")
async def open_update_password(callback: CallbackQuery, interface: Interface, state: FSMContext):
    await interface.basic_manager.input_password.open(state)


@basic_router.callback_query(F.data == "delete_password")
async def delete_password(callback: CallbackQuery, interface: Interface, state: FSMContext, session: ClientSession):
    await interface.basic_manager.options.delete_password(state, session)


@basic_router.message(StateFilter(States.input_password), F.text)
async def input_password(message: Message, interface: Interface, state: FSMContext):
    await interface.basic_manager.input_password(message.text, state)
    await message.delete()


@basic_router.message(StateFilter(States.repeat_password), F.text)
async def repeat_password(message: Message, interface: Interface, state: FSMContext):
    await interface.basic_manager.repeat_password(message.text, state)
    await message.delete()


@basic_router.message(StateFilter(States.input_email), F.text)
async def input_email(message: Message, interface: Interface, state: FSMContext):
    await interface.basic_manager.input_email(message.text, state)
    await message.delete()


@basic_router.message(StateFilter(States.input_verify_email_code), F.text)
async def input_verify_email_code(message: Message, interface: Interface, state: FSMContext, session: ClientSession):
    await interface.basic_manager.input_verify_email_code(message.text, state, session)
    await message.delete()


########################################################################################################################


@basic_router.callback_query(F.data == "change_notification_time")
async def open_change_notification_time(callback: CallbackQuery, interface: Interface, state: FSMContext):
    await interface.basic_manager.change_notification_hour.open(state)


@basic_router.callback_query(NotificationHourCallbackData.filter())
async def change_notification_time(callback: CallbackQuery, callback_data: NotificationHourCallbackData, interface: Interface, state: FSMContext):
    await interface.basic_manager.change_notification_hour(callback_data.hour, state)


@basic_router.callback_query(NotificationMinuteCallbackData.filter())
async def change_notification_time(callback: CallbackQuery, callback_data: NotificationMinuteCallbackData, interface: Interface, state: FSMContext, session: ClientSession):
    await interface.basic_manager.change_notification_minute(callback_data.minute, state, session)

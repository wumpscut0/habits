from frontend.routers import *

profile_router = Router()


@profile_router.callback_query(F.data == 'profile')
async def open_profile(callback: CallbackQuery, interface: Interface, state: FSMContext):
    await interface.profile.open_profile(callback.message.from_user.first_name, state)


@profile_router.callback_query(F.data == 'habits')
async def open_habits(callback: CallbackQuery, interface: Interface, state: FSMContext):
    await interface.habits

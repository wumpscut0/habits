

profile_router = Router()


@profile_router.callback_query(F.data == 'open_profile')
async def open_profile(message: Message, interface: Interface, state: FSMContext):
    await interface.update_interface(state, await interface.profile.update_hello(message.from_user.full_name))

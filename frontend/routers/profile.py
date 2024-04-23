from aiogram import Router, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiohttp import ClientSession
from frontend.FSM import States
from frontend.markups.interface import Interface
from frontend.routers.password import password_router

profile_router = Router()
profile_router.include_routers(password_router)


@profile_router.message(CommandStart())
async def open_authorization(message: Message, interface: Interface, session: ClientSession, state: FSMContext):
    await interface.close_session(state)
    async with session.post('/sign_in', json={'telegram_id': interface.chat_id}) as response:
        if response.status == 400:
            await interface.open_session(state, interface.profile.sign_in_with_password)
        elif response.status == 200:
            await interface.open_session(state, await interface.profile.update_hello(message.from_user.full_name))
        else:
            await message.answer('Internal server error')
    await message.delete()


@profile_router.message(StateFilter(States.sign_in_with_password), F.text)
async def sign_in_with_password(message: Message, interface: Interface, session: ClientSession, state: FSMContext):
    token = interface.profile.sign_in_with_password.sign_in_with_password(session, message.text, interface.chat_id)
    if token is not None:
        interface.token = token
        await interface.update_interface(state, interface.profile)
    await message.delete()


@profile_router.callback_query(F.data == 'open_profile')
async def open_profile(message: Message, interface: Interface, state: FSMContext):
    await interface.update_interface(state, await interface.profile.update_hello(message.from_user.full_name))

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiohttp import ClientSession
from frontend.FSM import States
from frontend.markups.interface import Interface


password_router = Router()


@password_router.callback_query(F.data == 'open_input_password')
async def open_input_password(message: Message, interface: Interface, state: FSMContext):
    await interface.update_interface(state, interface.profile.input_password)


@password_router.message(StateFilter(States.input_password), F.text)
async def input_password(message: Message, interface: Interface, state: FSMContext):
    await interface.update_interface(state, await interface.profile.input_password.input_password(message.text))
    await message.delete()


@password_router.message(StateFilter(States.repeat_password), F.text)
async def repeat_password(message: Message, interface: Interface, state: FSMContext):
    await interface.update_interface(state, await interface.profile.input_password.repeat_password(message.text))
    await message.delete()


@password_router.callback_query(F.data == 'open_warning')
async def open_warning(message: Message, interface: Interface, state: FSMContext):
    await interface.update_interface(state, interface.profile.input_password.password_resume.password_warning)


@password_router.callback_query(F.data == 'update_password')
async def update_password(message: Message, interface: Interface, state: FSMContext, session: ClientSession):
    async with session.patch('/update_password', headers={"Authorization": interface.token}) as response:
        if response.status != 200:
            await interface.close_session('No authorized. Try sign in: /start')
        else:
            await interface.update_interface(state, await interface.profile.add_exit_button())

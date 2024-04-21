from aiogram import Router, F
from aiogram.filters import StateFilter

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from frontend.markups.interface import Interface, States
from frontend.markups.password import InputPassword

password_router = Router()


@password_router.callback_query(F.data == 'open_input_password')
async def open_input_password(interface: Interface):
    await interface.update_interface(interface.profile.input_password)


@password_router.message(StateFilter(States.input_password), F.text)
async def input_password_(message: Message, interface: Interface):
    await interface.update_interface(interface.profile.input_password.input_password(message.text))


@password_router.message(StateFilter(States.repeat_password), F.text)
async def repeat_password(message: Message, interface: Interface):
    await interface.update_interface(interface.profile.input_password.repeat_password(message.text))

@password_router.callback_query(F.data == 'open_warning'):



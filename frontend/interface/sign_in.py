from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from frontend.FSM import SignInState
from frontend.interface import update_interface, update_text_message_by_bot, update_text_by_message
from frontend.markups.interface import Interface
from frontend.markups.sign_in import SignIn


sign_in_router = Router()


@sign_in_router.callback_query(F.data == 'open_sign_in')
async def open_sign_in(callback: CallbackQuery, state: FSMContext, interface: Interface):
    sign_in: SignIn = interface.authorization.sign_in

    await sign_in.reset(state)

    await update_interface(interface, state)

    await update_text_by_message(sign_in, callback.message)


@sign_in_router.message(StateFilter(SignInState.input_login), F.text)
async def input_login(message: Message, state: FSMContext, interface: Interface, message_id: int):
    sign_in: SignIn = interface.authorization.sign_in

    await sign_in.input_login(message.text)

    await update_interface(interface, state)

    await update_text_message_by_bot(sign_in, message_id, message.chat.id)

    await message.delete()


@sign_in_router.message(StateFilter(SignInState.input_password), F.text)
async def input_password(message: Message, state: FSMContext, interface: Interface, message_id: int):
    sign_in: SignIn = interface.authorization.sign_in

    await sign_in.input_password(message.text)

    await update_interface(interface, state)

    await update_text_message_by_bot(sign_in, message_id, message.chat.id)

    await message.delete()


@sign_in_router.callback_query(F.data == 'mode_sign_in')
async def mode_sign_in(callback: CallbackQuery, state: FSMContext, interface: Interface):
    sign_in: SignIn = interface.authorization.sign_in

    await sign_in.invert_input_mode(state)

    await update_interface(interface, state)

    await update_text_by_message(sign_in, callback.message)




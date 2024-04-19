from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiohttp import ClientSession
from frontend.FSM import User
from frontend.interface import update_interface, update_text_message_by_bot, update_text_by_message
from frontend.markups.interface import Interface
from frontend.markups.sign_up import SignUp, Nickname, Login, Password

sign_up_router = Router()


@sign_up_router.callback_query(F.data == 'open_sign_up')
async def open_sign_up(callback: CallbackQuery, state: FSMContext, interface: Interface):
    await state.set_state(None)

    sign_up: SignUp = interface.authorization.sign_up

    await update_text_by_message(sign_up, callback.message)


@sign_up_router.callback_query(F.data == 'open_nickname')
async def open_nickname(callback: CallbackQuery, state: FSMContext, interface: Interface):
    await state.set_state(User.input_nickname)

    nickname: Nickname = interface.authorization.sign_up.nickname

    await update_text_by_message(nickname, callback.message)


@sign_up_router.message(StateFilter(User.input_nickname), F.text)
async def input_nickname(message: Message, state: FSMContext, interface: Interface, message_id):
    nickname: Nickname = interface.authorization.sign_up.nickname

    await nickname.update_nickname(message.text)

    await update_interface(interface, state)

    await update_text_message_by_bot(nickname, message_id, message.chat.id)

    await message.delete()


@sign_up_router.callback_query(F.data == 'open_login')
async def open_login(callback: CallbackQuery, state: FSMContext, interface: Interface):
    await state.set_state(User.input_login)

    login: Login = interface.authorization.sign_up.login

    await update_text_by_message(login, callback.message)


@sign_up_router.message(StateFilter(User.input_login), F.text)
async def input_login(message: Message, state: FSMContext, session: ClientSession, interface: Interface, message_id):
    login: Login = interface.authorization.sign_up.login

    await login.update_login(message.text, session)

    await update_interface(interface, state)

    await update_text_message_by_bot(login, message_id, message.chat.id)

    await message.delete()


@sign_up_router.callback_query(F.data == 'open_password')
async def open_password(callback: CallbackQuery, state: FSMContext, interface: Interface):
    await state.set_state(User.input_password)

    password: Password = interface.authorization.sign_up.password

    await update_text_by_message(password, callback.message)


@sign_up_router.message(StateFilter(User.input_password), F.text)
async def input_password(message: Message, state: FSMContext, interface: Interface, message_id: int):
    await state.set_state(User.repeat_password)

    password: Password = interface.authorization.sign_up.password

    await password.update_password(message.text)

    await update_interface(interface, state)

    await update_text_message_by_bot(password, message_id, message.chat.id)

    await message.delete()


@sign_up_router.message(StateFilter(User.repeat_password), F.text)
async def repeat_password(message: Message, state: FSMContext, interface: Interface, message_id: int):
    password: Password = interface.authorization.sign_up.password

    await password.repeat_password(message.text)

    await update_interface(interface, state)

    await update_text_message_by_bot(password, message_id, message.chat.id)

    await message.delete()


@sign_up_router.callback_query(F.data == 'mode_password')
async def mode_password(callback: CallbackQuery, state: FSMContext, interface: Interface, message_id: int):
    password: Password = interface.authorization.sign_up.password

    if await state.get_state() == 'User:input_password':
        await state.set_state(User.repeat_password)
    else:
        await state.set_state(User.input_password)

    await password.invert_input_mode()

    await update_interface(interface, state)

    await update_text_by_message(password, callback.message)


@sign_up_router.callback_query(F.data == 'try_sign_up')
async def accept_sign_up(callback: CallbackQuery, state: FSMContext, session: ClientSession, interface: Interface):
    sign_up: SignUp = interface.authorization.sign_up

    await sign_up.try_sign_up(callback.message.from_user.id, session)

    await update_interface(interface, state)

    await update_text_by_message(sign_up, callback.message)


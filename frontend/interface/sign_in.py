from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.methods import AnswerCallbackQuery
from aiogram.types import CallbackQuery, Message

from frontend import bot
from frontend.FSM import User
from frontend.markups.sign_in import SignIn, Nickname, Login, Password
from frontend.utils import deserialize

sign_in_router = Router()


@sign_in_router.callback_query(F.data == 'sign_in')
async def open_sign_in(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    current_data = await state.get_data()
    sign_in: SignIn = await deserialize(current_data['sign_in'])
    await sign_in.update_sign_in()
    current_data['sign_in'] = await sign_in.serialize()
    await state.update_data(current_data)
    await callback.message.edit_text(text=await sign_in.text, reply_markup=await sign_in.markup)


@sign_in_router.callback_query(F.data == 'sign_in_nickname')
async def open_nickname(callback: CallbackQuery, state: FSMContext):
    await state.set_state(User.input_nickname)

    sign_in: SignIn = await deserialize((await state.get_data())['sign_in'])
    nickname: Nickname = sign_in.nickname
    await callback.message.edit_text(text=await nickname.text, reply_markup=await nickname.markup)


@sign_in_router.message(StateFilter(User.input_nickname), F.text)
async def input_nickname(message: Message, state: FSMContext):
    current_data = await state.get_data()
    sign_in: SignIn = await deserialize(current_data['sign_in'])
    nickname: Nickname = sign_in.nickname
    await nickname.update_nickname(message.text)
    current_data['sign_in'] = await sign_in.serialize()
    await state.update_data(current_data)

    try:
        await bot.edit_message_text(chat_id=message.chat.id, message_id=current_data['message_id'], text=await nickname.text, reply_markup=await nickname.markup)
    except TelegramBadRequest:
        pass

    await message.delete()


@sign_in_router.callback_query(F.data == 'sign_in_login')
async def open_login(callback: CallbackQuery, state: FSMContext):
    await state.set_state(User.input_login)

    sign_in_: SignIn = await deserialize((await state.get_data())['sign_in'])
    login: Login = sign_in_.login
    await callback.message.edit_text(text=await login.text, reply_markup=await login.markup)


@sign_in_router.message(StateFilter(User.input_login), F.text)
async def input_login(message: Message, state: FSMContext):
    current_data = await state.get_data()
    sign_in: SignIn = await deserialize(current_data['sign_in'])
    login: Login = sign_in.login
    await login.update_login(message.text)
    await message.delete()

    current_data['sign_in'] = await sign_in.serialize()
    await state.update_data(current_data)

    try:
        await message.edit_text(text=await login.text, reply_markup=await login.markup)
    except TelegramBadRequest:
        pass


@sign_in_router.callback_query(F.data == 'sign_in_password')
async def open_password(callback: CallbackQuery, state: FSMContext):
    await state.set_state(User.input_password)

    sign_in: SignIn = await deserialize((await state.get_data())['sign_in'])
    password: Password = sign_in.password
    await callback.message.edit_text(text=await password.text, reply_markup=await password.markup)


@sign_in_router.message(StateFilter(User.input_password), F.text)
async def input_password(message: Message, state: FSMContext):
    current_data = await state.get_data()
    sign_in: SignIn = await deserialize(current_data['sign_in'])
    password: Password = sign_in.password
    await password.update_password(message.text)
    await message.delete()

    current_data['sign_in'] = await sign_in.serialize()
    await state.update_data(current_data)

    try:
        await message.edit_text(text=await password.text, reply_markup=await password.markup)
    except TelegramBadRequest:
        pass


@sign_in_router.message(StateFilter(User.repeat_password), F.text)
async def repeat_password(message: Message, state: FSMContext):
    current_data = await state.get_data()
    sign_in: SignIn = await deserialize(current_data['sign_in'])
    password: Password = sign_in.password
    await password.repeat_password(message.text)
    await message.delete()

    current_data['sign_in'] = await sign_in.serialize()
    await state.update_data(current_data)

    try:
        await message.edit_text(text=await password.text, reply_markup=await password.markup)
    except TelegramBadRequest:
        pass


@sign_in_router.callback_query(F.data == 'mode_password')
async def open_password(callback: CallbackQuery, state: FSMContext):
    current_data = await state.get_data()
    sign_in: SignIn = await deserialize(current_data['sign_in'])
    password: Password = sign_in.password

    if await state.get_state() == 'input_password':
        await state.set_state(User.repeat_password)
        await password.repeat_password_state()
    else:
        await state.set_state(User.input_password)
        await password.password_input_state()

    current_data['sign_in'] = await sign_in.serialize()
    await state.update_data(current_data)

    await callback.message.edit_text(text=await password.text, reply_markup=await password.markup)




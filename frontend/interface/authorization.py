from typing import Dict

from aiogram import Router, F
from aiogram.filters import CommandStart, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from frontend import bot
from frontend.interface import update_interface, close_session, refill_trash, update_text_by_message
from frontend.interface.sign_up import sign_up_router
from frontend.markups.authorization import Authorization
from frontend.markups.interface import Interface
from frontend.markups.sign_up import SignUp

authorization_router = Router()
authorization_router.include_routers(
    sign_up_router
)


@authorization_router.message(CommandStart())
async def open_authorization(message: Message, state: FSMContext, interface: Interface, message_id: int):
    await state.set_state(None)

    message_id = await close_session(message.chat.id, message_id)

    if isinstance(message_id, int):
        await refill_trash(message_id, state)

    authorization: Authorization = interface.authorization

    message = await message.answer(text=await authorization.text, reply_markup=await authorization.markup)

    await state.update_data({'message_id': message.message_id})

    await update_interface(interface, state)


@authorization_router.callback_query(F.data == 'open_authorization')
async def open_authorization(callback: CallbackQuery, state: FSMContext, interface: Interface):
    await state.set_state(None)

    await update_text_by_message(interface.authorization, callback.message)

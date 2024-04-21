from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiohttp import ClientSession

from frontend.FSM import SignInState
from frontend.interface import update_interface, update_text_message_by_bot, update_text_by_message
from frontend.markups.interface import Interface
from frontend.markups.sign_in import SignIn

profile_router = Router()


@profile_router.callback_query(F.data == 'open_profile')
async def open_profile(callback: CallbackQuery, state: FSMContext, interface: Interface, session: ClientSession):
    await state.set_state(None)

    sign_in: SignIn = interface.profile.sign_in

    success = await sign_in.try_sign_in(session)

    await update_interface(interface, state)

    if not success:
        await update_text_by_message(sign_in, callback.message)
    else:
        await update_text_by_message(sign_in.profile, callback.message)



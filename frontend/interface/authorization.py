from typing import Dict

from aiogram import Router, F
from aiogram.filters import CommandStart, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from frontend import bot
from frontend.interface import update_interface, close_session, refill_trash, update_text_by_message
from frontend.interface.sign_up import sign_up_router
from frontend.markups.authorization import Profile
from frontend.markups.interface import Interface
from frontend.markups.sign_up import SignUp

authorization_router = Router()
authorization_router.include_routers(
    sign_up_router
)


@authorization_router.message(CommandStart())
async def open_authorization(interface: Interface):
    await interface.open_session()


@authorization_router.callback_query(F.data == 'open_profile')
async def open_authorization(interface: Interface):
    await interface.open_session()

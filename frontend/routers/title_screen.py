from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiohttp import ClientSession

from frontend.markups.interface import Interface

title_screen = Router()


@title_screen.message(CommandStart())
async def tittle_screen(message: Message, interface: Interface, state: FSMContext):
    await interface.open_session(state)
    await message.delete()


@title_screen.callback_query(F.data == 'title_screen')
async def tittle_screen(callback: CallbackQuery, interface: Interface, state: FSMContext):
    await interface.update(state, interface.title_screen)


@title_screen.callback_query(F.data == 'invert_notifications')
async def invert_notifications(callback: CallbackQuery, interface: Interface, state: FSMContext, session: ClientSession):
    await interface.title_screen.invert_notifications(session, state)


@title_screen.callback_query(F.data == 'authorization')
async def authorization(callback: CallbackQuery, interface: Interface, state: FSMContext, session: ClientSession):
    await interface.title_screen.authorization(session, state)

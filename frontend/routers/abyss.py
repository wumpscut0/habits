from aiogram import Router, F
from aiogram.filters import StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, BotCommand

from frontend.controller import Interface


abyss_router = Router()


@abyss_router.message(Command(BotCommand(command='clear', description='Clear current state')))
async def clear(message: Message, interface: Interface, state: FSMContext):
    await interface.clear(state)
    await message.delete()


@abyss_router.message(StateFilter(None), ~F.text.startswith('/'))
async def abyss(message: Message):
    await message.delete()





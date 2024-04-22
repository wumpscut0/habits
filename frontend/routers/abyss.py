from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, BotCommand
from aiogram.filters import Command


abyss_router = Router()


@abyss_router.message(Command(BotCommand(command='clear', description='Clear current state')))
async def clear(message: Message, state: FSMContext):
    await state.clear()
    await message.delete()


@abyss_router.message(StateFilter(None))
async def abyss(message: Message):
    await message.delete()





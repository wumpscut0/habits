from typing import List

from aiogram import F, Router
from aiogram.filters import or_f, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import config
from frontend.interface import close_session, refill_trash, kill_message, update_text_by_message

abyss_router = Router()


@abyss_router.message(or_f(F.text.in_(config.COMMANDS), ~F.text, StateFilter(None)))
async def abyss(message: Message, state: FSMContext, message_id: int):
    if message.text == 'clear':
        message_id = await close_session(message.chat.id, message_id)
        if isinstance(message_id, int):
            trash = await refill_trash(message_id, state)
        await state.clear()
        await state.update_data({'trash': trash})
    if message.text == 'status':
        status = await state.get_state()
        new_message = await message.answer(text=status if status is not None else 'None')
        await refill_trash(new_message.message_id, state)

    # if message.text == 'update':
    #     await update_text_by_message(message.)

    await message.delete()

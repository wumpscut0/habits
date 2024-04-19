from typing import Any

from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from frontend.markups import Markup
from frontend.markups.interface import Interface
from frontend import bot


async def update_interface(interface: Interface, state: FSMContext):
    await state.update_data({'interface': await interface.serialize()})


async def update_text_message_by_bot(markup: Markup, message_id: int, chat_id: int):
    try:
        await bot.edit_message_text(
            text=await markup.text,
            reply_markup=await markup.markup,
            message_id=message_id,
            chat_id=chat_id
        )
    except TelegramBadRequest:
        pass


async def update_text_by_message(markup: Markup, message: Message):
    try:
        await message.edit_text(text=await markup.text, reply_markup=await markup.markup)
    except TelegramBadRequest:
        pass


async def close_session(chat_id, message_id):
    try:
        message = await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text='Session close'
        )
        return message.message_id
    except TelegramBadRequest:
        return 'Open session not found'


async def kill_message(chat_id, message_id):
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except TelegramBadRequest:
        return 'Message for delete not found'


async def refill_trash(message_id: int, state: FSMContext):
    trash = (await state.get_data())['trash']
    trash.append(message_id)
    await state.update_data({'trash': trash})
    return trash



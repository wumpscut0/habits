from aiogram.utils.formatting import Bold

from frontend.markups import *
from aiogram.types.inline_keyboard_markup import InlineKeyboardMarkup, InlineKeyboardButton


async def remainder(chat_id: int, ):
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f'{Emoji.OK} Ok', callback_data="close_notification"),
            ]
        ]
    )
    bot.send_message(chat_id=chat_id, text=Bold('Don`t forget mark done target today'), reply_markup=markup)

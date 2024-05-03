from aiogram.utils.formatting import Bold
from aiogram.types.inline_keyboard_markup import InlineKeyboardMarkup, InlineKeyboardButton

from frontend import bot
from frontend.markups import Emoji

remainder_text = Bold('Don`t forget mark done target today')
remainder_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f'{Emoji.OK} Ok', callback_data="close_notification"),
            ]
        ]
    )

async def remainder(chat_id: int):
    # OFF THIS JOB IF USER DONE ALL
    bot.send_message(chat_id=chat_id, text="", reply_markup=remainder_markup)

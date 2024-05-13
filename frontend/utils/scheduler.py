import os

import pytz
from pytz import utc

import aiohttp
import jwt
from aiogram.types import InlineKeyboardButton
from aiogram.utils.formatting import Bold
from aiogram.types.inline_keyboard_markup import InlineKeyboardMarkup
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore

from frontend.bot import bot
from frontend.utils import config, Emoji, get_service_key
from frontend.utils.loggers import info

remainder_text = Bold('Don`t forget mark done target today').as_html()
remainder_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f'{Emoji.OK} Ok', callback_data="close_notification"),
            ]
        ]
    )


async def remainder(chat_id: int):
    info.info(f'Remaining sent to user {chat_id}')
    await bot.send_message(chat_id=chat_id, text=remainder_text, reply_markup=remainder_markup)


async def increase_progress():
    info.info(f'Progress increased')
    key = await get_service_key()
    async with aiohttp.ClientSession() as session:
        async with session.patch(os.getenv('BACKEND') + f'/increase_targets_progress/{key}') as response:
            for user_id in (await response.json()):
                scheduler.add_job(remainder,  args=(user_id,), replace_existing=True, id=user_id)


DEFAULT_REMAINING_HOUR = config.getint('limitations', "DEFAULT_REMAINING_HOUR")

jobstores = {
    'default': RedisJobStore(host='localhost', port=6379, db=1)
}

scheduler = AsyncIOScheduler()
# pytz.timezone('Asia/Novosibirsk')
scheduler.configure(jobstores=jobstores)

scheduler.add_job(increase_progress, 'cron', hour=0, replace_existing=True, id="increase_progress")


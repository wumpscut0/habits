import os
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
from frontend.utils import config, Emoji


remainder_text = Bold('Don`t forget mark done target today')
remainder_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f'{Emoji.OK} Ok', callback_data="close_notification"),
            ]
        ]
    )


async def remainder(chat_id: int):
    bot.send_message(chat_id=chat_id, text=remainder_text, reply_markup=remainder_markup)


async def increase_progress():
    signature = jwt.encode({"password": os.getenv('SERVICES_PASSWORD')}, os.getenv('JWT'))
    async with aiohttp.ClientSession() as session:
        await session.patch(os.getenv('BACKEND') + f'/increase_targets_progress/{signature}')
        async with session.get(os.getenv('BACKEND') + f'/users_ids/{signature}') as response:
            for user_id in (await response.json()):
                scheduler.add_job(remainder,  replace_existing=True, id=user_id)


async def reset_verify_code(interface):
    interface.storage.update({"verify_code": None, "email": None})


DEFAULT_REMAINING_HOUR = config.getint('limitations', "DEFAULT_REMAINING_HOUR")

jobstores = {
    'default': RedisJobStore(host='localhost', port=6379, db=1)
}
executors = {
    'default': ThreadPoolExecutor(max_workers=1000)
}
job_defaults = {
    'coalesce': False,
    'max_instances': 1
}

scheduler = AsyncIOScheduler()
scheduler.configure(jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone=utc)
scheduler.add_job(increase_progress, 'cron', hour=0, replace_existing=True, id="increase_progress")
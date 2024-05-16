import os

import aiohttp

from aiogram.types import InlineKeyboardButton
from aiogram.utils.formatting import Bold
from aiogram.types.inline_keyboard_markup import InlineKeyboardMarkup
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore

from client.bot import bot
from client.utils import Emoji
from client.utils.loggers import info, errors
from client.utils.redis import Storage

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
    async with aiohttp.ClientSession() as session:
        async with session.patch(
                os.getenv('BACKEND') + f'/targets/progress',
                headers={"Authorization": await Storage.storage.get("service_key")}
        ) as response:
            if response.status == 200:
                info.info(f'Progress increased')
                for user_id in (await response.json()):
                    scheduler.add_job(remainder, args=(user_id,), replace_existing=True, id=user_id)
            else:
                errors.error(f"Progress not increased. Status {response.status}")


jobstores = {
    'default': RedisJobStore(db=2)
}

scheduler = AsyncIOScheduler()
scheduler.configure(jobstores=jobstores)

scheduler.add_job(increase_progress, 'cron', hour=14, minute=15, replace_existing=True, id="increase_progress")

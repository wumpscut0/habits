import os
import logging
import pickle

import aiohttp
import jwt
from dotenv import load_dotenv, find_dotenv
from configparser import ConfigParser
from logging.config import dictConfig
from base64 import b64decode, b64encode
from pytz import utc

from aiogram import Bot
from aiogram import Dispatcher
from aiogram.fsm.storage.redis import RedisStorage, Redis
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore

from frontend.controller import Interface
from frontend.markups.remainder import remainder
from frontend.routers.abyss import abyss_router
from frontend.middlewares import CommonMiddleware
from frontend.routers.profile import profile_router


class Emoji:
    OK = "✅"
    DENIAL = "❌"
    BACK = "⬇️"
    KEY = "🔑"
    DOOR = "🚪"
    BRAIN = "🧠"
    MEGAPHONE = "📢"
    SHINE_STAR = "🌟"
    WARNING = "⚠️"
    SHIELD = "🛡"
    CYCLE = "🔄"
    BELL = "🔔"
    NOT_BELL = "🔕"
    EYE = "👁"
    SPROUT = "🌱"
    DIAGRAM = "📊"
    BULB = "💡"
    GEAR = "⚙"
    ENVELOPE = "✉️"
    LOCK_AND_KEY = "🔐"
    PLUS = "➕"
    UP = "🆙"
    SKIP = "⏭️"
    GREEN_BIG_SQUARE = "🟩"
    GREY_BUG_SQUARE = "⬜️"
    RED_QUESTION = "❓"
    GREY_QUESTION = "❔"
    BAN = "🚫"
    GREEN_CIRCLE = "🟢"
    YELLOW_CIRCLE = "🟡"
    ORANGE_CIRCLE = "🟠"
    RED_CIRCLE = "🔴"
    FLAG_FINISH = "🏁"
    DART = "🎯"
    REPORT = "🧾"
    LIST_WITH_PENCIL = "📝"
    NEW = "🆕"
    TROPHY = "🏆"
    CLOCK = "🕒"


class SerializableMixin:
    async def serialize(self):
        return b64encode(pickle.dumps(self)).decode()


async def deserialize(sequence: str):
    return pickle.loads(b64decode(sequence.encode()))


async def increase_progress():
    signature = jwt.encode({"password": os.getenv('SERVICES_PASSWORD')}, os.getenv('JWT'))
    async with aiohttp.ClientSession() as session:
        await session.patch(os.getenv('BACKEND') + f'/increase_targets_progress/{signature}')
        async with session.get(os.getenv('BACKEND') + f'/users_ids/{signature}') as response:
            for user_id in (await response.json()):
                scheduler.add_job(remainder,  replace_existing=True, id=user_id)


async def reset_verify_code(interface):
    interface.storage.update({"verify_code": None, "email": None})


load_dotenv(find_dotenv())

bot = Bot(os.getenv('TOKEN'), parse_mode='HTML')

dispatcher = Dispatcher(storage=RedisStorage(Redis()))
dispatcher.update.middleware(CommonMiddleware())
dispatcher.include_routers(
    abyss_router,
    profile_router,
)

config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": '%(asctime)s | %(message)s'
        }
    },
    "handlers": {
        "errors": {
            "class": "logging.FileHandler",
            "formatter": "default",
            "filename": "errors.log",
        },
        "info": {
            "class": "logging.FileHandler",
            "formatter": "default",
            "filename": "info.log",
        }
    },
    "loggers": {
        "errors": {
            "level": logging.ERROR,
            "handlers": [
                "errors"
            ]
        },
        "info": {
            "level": logging.INFO,
            "handlers": [
                "info"
            ]
        },
    }
}

dictConfig(config)

errors = logging.getLogger("errors")
info = logging.getLogger('info')

config = ConfigParser()

config.read('./config.ini')

DEFAULT_REMAINING_HOUR = config.get('limitations', "DEFAULT_REMAINING_HOUR")

jobstores = {
    'default': RedisJobStore(host='localhost', port=6380, db=1)
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

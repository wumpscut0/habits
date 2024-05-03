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
from frontend.routers.abyss import abyss_router
from frontend.middlewares import CommonMiddleware
from frontend.routers.profile import profile_router


class SerializableMixin:
    async def serialize(self):
        return b64encode(pickle.dumps(self)).decode()


async def deserialize(sequence: str):
    return pickle.loads(b64decode(sequence.encode()))


async def increase_progress():
    signature = jwt.encode({"password": os.getenv('SERVICES_PASSWORD')}, os.getenv('JWT'))
    async with aiohttp.ClientSession() as session:
        await session.patch(os.getenv('BACKEND') + f'/increase_habits_progress/{signature}')


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
scheduler.add_job(increase_progress, 'cron', hour=0)

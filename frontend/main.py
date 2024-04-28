import asyncio
from asyncio import run
from aiogram import Dispatcher
from aiogram.fsm.storage.redis import RedisStorage, Redis
from apscheduler.executors.pool import ThreadPoolExecutor
from pytz import utc

from frontend import bot
from frontend.routers.abyss import abyss_router
from frontend.middlewares import CommonMiddleware
from frontend.routers.profile import profile_router
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore

dispatcher = Dispatcher(storage=RedisStorage(Redis()))
dispatcher.update.middleware(CommonMiddleware())
dispatcher.include_routers(
    abyss_router,
    profile_router,
)

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

remainder = AsyncIOScheduler()
remainder.configure(jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone=utc)


async def main():
    await asyncio.gather(remainder.start(), dispatcher.start_polling(bot))


if __name__ == '__main__':
    run(main())

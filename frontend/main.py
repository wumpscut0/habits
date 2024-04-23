from asyncio import run
from aiogram import Dispatcher
from aiogram.fsm.storage.redis import RedisStorage, Redis
from frontend import bot
from frontend.routers.abyss import abyss_router
from frontend.middlewares import CommonMiddleware
from frontend.routers.profile import profile_router

dispatcher = Dispatcher(storage=RedisStorage(Redis()))
dispatcher.update.middleware(CommonMiddleware())
dispatcher.include_routers(
    abyss_router,
    profile_router,
)


async def main():
    await dispatcher.start_polling(bot)


if __name__ == '__main__':
    run(main())

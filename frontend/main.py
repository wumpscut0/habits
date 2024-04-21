from asyncio import run
from aiogram import Dispatcher
from aiogram.fsm.storage.redis import RedisStorage, Redis
from frontend import bot
from frontend.interface.abyss import abyss_router
from frontend.interface.authorization import authorization_router
from frontend.interface.profile import profile_router
from frontend.interface.sign_in import sign_in_router
from frontend.middlewares import CommonMiddleware

dispatcher = Dispatcher(storage=RedisStorage(Redis()))
dispatcher.update.middleware(CommonMiddleware())
dispatcher.include_routers(
    authorization_router,
    abyss_router,
    sign_in_router,
    profile_router
)


async def main():
    await dispatcher.start_polling(bot)

if __name__ == '__main__':
    run(main())

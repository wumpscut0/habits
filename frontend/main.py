from asyncio import run
from aiogram import Dispatcher
from aiogram.fsm.storage.redis import RedisStorage, Redis
from frontend import bot
from frontend.interface.abyss import router_abyss
from frontend.interface.authorization import authorization_router
from frontend.middlewares import CommonMiddleware


dispatcher = Dispatcher(storage=RedisStorage(Redis()))
dispatcher.update.middleware(CommonMiddleware())
dispatcher.include_routers(
    authorization_router,
    router_abyss,
)


async def main():
    await dispatcher.start_polling(bot)

if __name__ == '__main__':
    run(main())

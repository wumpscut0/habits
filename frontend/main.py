from asyncio import run
from aiogram import Dispatcher, F, Router
from aiogram.fsm.storage.redis import RedisStorage, Redis
from aiogram.types import Message

from frontend import bot
from frontend.interface import authorization_router
abyss = Router()
dispatcher = Dispatcher(storage=RedisStorage(Redis()))
dispatcher.include_routers(
    authorization_router,
    abyss,
)


@abyss.message(F)
async def abyss(message: Message):
    await message.delete()


async def main():
    await dispatcher.start_polling(bot)

if __name__ == '__main__':
    run(main())

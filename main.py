from asyncio import run
from os import getenv
from aiogram import Dispatcher, Bot
from aiogram.filters import CommandStart
from aiogram.fsm.storage.redis import RedisStorage, Redis
from aiogram.types import Message
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
dispatcher = Dispatcher(storage=RedisStorage(Redis()))

bot = Bot(getenv('TOKEN'))


@dispatcher.message(CommandStart())
async def open_menu(message: Message):
    await message.answer('Congratulation! You configurated elephant and whale and you understand poetry')


async def main():
    await dispatcher.start_polling()

if __name__ == '__main__':
    run(main())

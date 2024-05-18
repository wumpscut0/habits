import asyncio
import os

from aiogram.types import BotCommand
from aiohttp import ClientSession

from client.bot.dispatcher import dispatcher
from client.bot import BotControl, BotCommands
from client.utils.loggers import errors, info
from client.utils.redis import Storage
from client.utils.scheduler import scheduler


async def main():
    scheduler.start()
    await BotControl.bot.set_my_commands(BotCommands)
    await dispatcher.start_polling(BotControl.bot)


if __name__ == '__main__':
    asyncio.run(main())

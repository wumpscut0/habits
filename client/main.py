import asyncio
import os

from aiogram.types import BotCommand
from aiohttp import ClientSession

from client.bot.dispatcher import dispatcher
from client.bot import bot
from client.utils.loggers import errors, info
from client.utils.redis import Storage
from client.utils.scheduler import scheduler


async def main():
    scheduler.start()

    await bot.set_my_commands(
        [
            BotCommand(
                command="/start",
                description="Get title screen"
            ),
            BotCommand(
                command="/clear",
                description="Reset current state"
            )
        ]
    )
    await dispatcher.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())

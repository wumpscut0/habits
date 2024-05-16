import asyncio
import os

from aiogram.types import BotCommand
from aiohttp import ClientSession

from client.bot.dispatcher import dispatcher
from client.bot import bot
from client.utils import storage
from client.utils.loggers import errors, info
from client.utils.scheduler import scheduler


async def main():
    scheduler.start()
    async with ClientSession(os.getenv("BACKEND")) as session:
        async with session.post("/services/login", json={"password": os.getenv("SERVICE_KEY")}) as response:
            if response.status == 200:
                storage.set("service_key", await response.text())
                info.info("Access to the server has been granted")
            elif response.status == 401:
                errors.critical((await response.json())["detail"])
            elif response.status == 500:
                errors.critical("Internal server error")
            else:
                errors.critical(f"Unknown error with try authorization on server. Status: {response.status}")

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

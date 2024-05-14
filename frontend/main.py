import asyncio
import os

from aiogram.types import BotCommand
from aiohttp import ClientSession

from frontend.bot.dispatcher import dispatcher
from frontend.bot import bot
from frontend.utils import storage
from frontend.utils.loggers import errors, info
from frontend.utils.scheduler import scheduler


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

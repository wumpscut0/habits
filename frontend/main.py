import asyncio

from aiogram.types import BotCommand

from frontend.bot.dispatcher import dispatcher
from frontend.bot import bot
from frontend.utils.scheduler import scheduler


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

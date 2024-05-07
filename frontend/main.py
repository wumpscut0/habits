import asyncio

from frontend.bot.dispatcher import dispatcher
from frontend.bot import bot
from frontend.utils.scheduler import scheduler


async def main():
    scheduler.start()
    await dispatcher.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())

import asyncio

from client.bot.dispatcher import dispatcher
from client.bot import BotControl, BotCommands
from client.utils.scheduler import Scheduler


async def main():
    Scheduler.scheduler.start()
    Scheduler.set_job_increase_progress()
    await BotControl.bot.set_my_commands(BotCommands.bot_commands)
    await dispatcher.start_polling(BotControl.bot)


if __name__ == "__main__":
    asyncio.run(main())

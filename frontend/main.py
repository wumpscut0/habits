import asyncio

from frontend import dispatcher, bot, scheduler


async def main():
    await asyncio.gather(scheduler.start(), dispatcher.start_polling(bot))


if __name__ == '__main__':
    asyncio.run(main())

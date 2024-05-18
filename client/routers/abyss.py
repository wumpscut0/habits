from aiogram import Router, F
from aiogram.filters import StateFilter, Command
from aiogram.types import Message, BotCommand

from client.bot import bot
from client.controller import Interface
from client.utils.scheduler import scheduler

abyss_router = Router()
commands = ["/clear", "/start", "/jobs"]


@abyss_router.message(Command(BotCommand(command='clear', description='Clear current state')))
async def clear(message: Message, interface: Interface):
    await interface.clear()
    await message.delete()


@abyss_router.message(Command(BotCommand(command='jobs', description="Current jobs")))
async def jobs(message: Message, interface: Interface):
    current_jobs = scheduler.get_jobs()
    jobs_ = ''
    for job in current_jobs:
        jobs_ += job.name + '\n' + str(job.next_run_time)
    message_ = await bot.send_message(chat_id=interface.user_id, text=jobs_)
    await interface.refill_trash(message_.message_id)
    await interface.update_interface_in_redis()
    await message.delete()


@abyss_router.message(StateFilter(None), ~F.text.in_(commands))
async def abyss(message: Message):
    await message.delete()

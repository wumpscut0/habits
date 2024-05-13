import datetime

from aiogram import Router, F
from aiogram.filters import StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, BotCommand

from frontend.bot import bot
from frontend.controller import Interface
from frontend.utils.scheduler import scheduler

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
        jobs_ += job.name + str(job.next_run_time) + '\n' + job.id
    message_ = await bot.send_message(chat_id=interface.chat_id, text=jobs_)
    await interface.refill_trash(message_.message_id)
    await interface.update_interface_in_redis()
    await message.delete()


@abyss_router.message(StateFilter(None), ~F.text.in_(commands))
async def abyss(message: Message):
    await message.delete()

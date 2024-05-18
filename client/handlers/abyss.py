from aiogram import Router, F
from aiogram.filters import StateFilter, Command
from aiogram.types import Message, BotCommand

from client.bot import BotControl, BotCommands
from client.markups.basic import Jobs
from client.markups.core import TextMessage, TextWidget
from client.utils.scheduler import scheduler

abyss_router = Router()


@abyss_router.message(BotCommands.exit)
async def exit_(message: Message, bot_control: BotControl):
    text_message = TextMessage()
    text_message.add_text_row(TextWidget('Good by!'))
    await bot_control.update_interface(text_message)
    await message.delete()


@abyss_router.message(BotCommands.jobs)
async def jobs(message: Message, bot_control: BotControl):
    await bot_control.update_interface(await Jobs().init(), temp=True)
    await message.delete()


@abyss_router.message(StateFilter(None), ~F.text.in_(BotCommands.str_commands()))
async def abyss(message: Message):
    await message.delete()

from aiogram import Router, F
from aiogram.filters import StateFilter, Command
from aiogram.types import Message, BotCommand

from client.bot import BotControl, BotCommands
from client.markups.basic import TitleScreen, Temp
from client.markups.core import TextMessageMarkup, TextWidget
from client.utils.scheduler import Jobs

commands_router = Router()


@commands_router.message(BotCommands.start())
async def start(message: Message, bot_control: BotControl):
    await message.delete()
    await bot_control.api.add_user(bot_control.user_id)
    await bot_control.update_text_message(await TitleScreen().init(bot_control.user_id))


@commands_router.message(BotCommands.exit())
async def exit_(message: Message, bot_control: BotControl):
    text_message = TextMessageMarkup()
    text_message.add_text_row(TextWidget(text='Good by!'))
    await bot_control.update_text_message(text_message)
    await message.delete()


@commands_router.message(BotCommands.jobs())
async def jobs(message: Message, bot_control: BotControl):
    await bot_control.update_text_message(await Jobs().init())
    await message.delete()

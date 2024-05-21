from aiogram import Router, F
from aiogram.filters import StateFilter, Command
from aiogram.types import Message, BotCommand

from client.bot import BotControl, BotCommands

from client.markups.core import TextMessageMarkup, TextWidget
from client.markups.specific import TitleScreen

commands_router = Router()


@commands_router.message(BotCommands.start())
async def start(message: Message, bot_control: BotControl):
    await message.delete()

    await bot_control.api.add_user(bot_control.user_id)
    bot_control.set_context(TitleScreen, bot_control.user_id)
    await bot_control.update_text_message(await TitleScreen(bot_control.user_id).init())


@commands_router.message(BotCommands.exit())
async def exit_(message: Message, bot_control: BotControl):
    await message.delete()

    markup = TextMessageMarkup()
    markup.add_text_row(TextWidget(text="Good by!"))
    await bot_control.update_text_message(markup)

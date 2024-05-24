from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message

from client.bot import BotControl, BotCommands
from client.bot.FSM import States
from client.markups import Conform, Input, Info

from client.markups.core import TextMessageMarkup, TextWidget
from client.markups.specific import TitleScreen
from client.utils import Emoji

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


@commands_router.message(BotCommands.report())
async def report(message: Message, bot_control: BotControl):
    await message.delete()

    await bot_control.update_text_message(Input(
        f"Enter your message {Emoji.PENCIL}",
        state=States.input_text_to_admin
    ))


@commands_router.message(StateFilter(States.input_text_to_admin), F.text)
async def send_message_to_admin_accept_input(message: Message, bot_control: BotControl):
    await bot_control.send_message_to_admin(message.text)
    await message.delete()
    await bot_control.update_text_message(Info(
        f"Message sent {Emoji.INCOMING_ENVELOPE}"
    ))

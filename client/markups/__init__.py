from aiogram import Bot
from aiogram.fsm.context import FSMContext

from client.bot import BotControl
from client.markups.core import TextMarkup


class TextMarkupBuilder

class MarkupContext:
    def __init__(self, bot: Bot, bot_control: BotControl, text_markup: TextMarkup, state: FSMContext):
        self._bot = bot
        self._bot_control = bot_control
        self._text_markup = text_markup
        self._state = state

    async def open(self, **kwargs):
        await self._text_markup.open(**kwargs)
        await self._state.set_state(self._text_markup.state)
        try:
            await self._bot.edit_message_text(
                chat_id=self._bot_control.chat_id,
                message_id=self._bot_control.storage.message_id,
                text=(await self._text_markup.text) + ('\n' + self.feedback.text.as_html() if self.feedback.active else ''),
                reply_markup=await markup.markup
            )
        except TelegramBadRequest:
            pass

        self.feedback.off()
        await self.clean_trash()
        await self.update_interface_in_redis()

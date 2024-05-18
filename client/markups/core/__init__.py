from abc import abstractmethod, ABC
from typing import List, Dict

from aiogram.filters import CommandStart
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State

from aiogram.types import InlineKeyboardButton, Message
from aiogram.utils.formatting import as_list, Text, Bold, Italic
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup

from client.api import ServerApi
from client.bot.FSM import States
from client.routers.basic import basic_router
from client.utils import Emoji
from client.bot import BotControl


# class Hideable:
#     def __init__(self, active=True):
#         self._active = active
#
#     def on(self):
#         self._active = True
#
#     def off(self):
#         self._active = False
#
#     @property
#     def active(self):
#         return self._active


# class Resettable:
#     def __init__(self, obj: Any):
#         self.obj = obj
#         self._default_attrs = {name: value for name, value in vars(self.obj).items() if not callable(value)}
#
#     async def reset(self):
#         for name, value in self._default_attrs.items():
#             setattr(self.obj, name, value)


class TextWidget:
    def __init__(self, text: str = None):
        self._text = text

    def __repr__(self):
        return self._text

    @property
    def text(self):
        if self._text is None:
            return Text(Emoji.BAN)

        return Bold(self._text)

    @text.setter
    def text(self, value):
        self._text = value


class DataTextWidget:
    def __init__(
            self,
            *,
            header: str = None,
            data: str = Emoji.GREY_QUESTION,
            mark: str = '',
            sep: str = ': ',
            end: str = '',
    ):
        self.header = header
        self.data = data
        self.mark = mark
        self.sep = sep
        self.end = end

    def __repr__(self):
        return self.text.as_html()

    @property
    def text(self):
        if self.header is None:
            return Text(Emoji.BAN)

        separator = '' if str(self.header).startswith(' ') else ' '
        return Text(self.mark) + Text(separator) + Bold(self.header) + Text(self.sep) + Italic(self.data) + Italic(
            self.end)


class ButtonWidget:
    def __init__(
            self,
            *,
            text: str = None,
            callback_data: str | CallbackData = None,
            mark: str = '',
    ):
        self._text = text
        self._callback_data = callback_data
        self.mark = mark

    @property
    def text(self):
        if not self._text:
            return Emoji.BAN

        separator = '' if self._text.startswith(' ') else ' '
        return self.mark + separator + self._text

    @text.setter
    def text(self, text):
        self._text = text

    @property
    def callback_data(self):
        if not self._callback_data:
            return Emoji.BAN
        return self._callback_data

    @callback_data.setter
    def callback_data(self, callback_data):
        self._callback_data = callback_data


# class PhotoMarkup:
#     def __init__(self):
#         self._photo: str | InputMediaPhoto | None = None
#
#     @property
#     def photo(self):
#         return self._photo
#
#     @photo.setter
#     def photo(self, photo: str | InputMediaPhoto):
#         self._photo = photo


class TextMap:
    def __init__(self):
        self._map = []

    def set_map(self, map_: List[DataTextWidget | TextWidget]):
        self._map = map_

    def add_string_row(self, text: DataTextWidget | TextWidget):
        self._map.append(text)

    @property
    def text(self):
        if not self._map:
            return Emoji.BAN
        return (as_list(*[text.text for text in self._map])).as_html()


class MarkupMap:
    """
    Max telegram inline keyboard buttons row is 8.
     add_button_in_last_row will automatically move the button to the new row
    """
    _limitation_row = 8

    def __init__(self):
        self._map = [[]]

    def set_map(self, map_: List[List[ButtonWidget]]):
        self._map = map_

    def add_button_in_last_row(self, button: ButtonWidget):
        if len(self._map[-1]) == self._limitation_row:
            self.add_button_in_new_row(button)
        else:
            self._map[-1].append(button)

    def add_button_in_new_row(self, button: ButtonWidget):
        self._map.append([button])

    @property
    def markup(self):
        if self._map == [[]]:
            return

        markup = InlineKeyboardBuilder()
        for buttons_row in self._map:
            row = InlineKeyboardBuilder()
            for button in buttons_row:
                row.button(text=button.text, callback_data=button.callback_data)
            markup.attach(row)
        return markup.as_markup()


@basic_router.message(CommandStart())
async def open_tittle_screen(message: Message, bot_control: BotControl):
    AuthenticationWithPasswordMarkup(bot_control)
    await message.delete()


class AuthenticationWithPasswordMarkup():
    _action = TextWidget(f'{Emoji.KEY} Enter the password')
    _reset_password = ButtonWidget(
        text=f'{Emoji.CYCLE} Reset password',
        callback_data='reset_password'
    )
    _back = ButtonWidget(
        text=f"{Emoji.BACK} Back",
        callback_data="title_screen"
    )

    def __init__(self, bot_control: BotControl):
        super().__init__(
            text_map=TextMap(
                [
                    self._action
                ],
            ),
            state=States.sign_in_with_password
        )

    async def open(self):
        text_markup = TextMarkup()
        markup_map = MarkupMap()
        response = await self.api.get_user()
        if response.status == 200 and (await response.json()).get("email"):
            markup_map.add_button_in_new_row(self._reset_password)
        markup_map.add_button_in_new_row(self._back)
        self.markup_map = markup_map
from aiogram import Bot
from aiogram.fsm.context import FSMContext

from client.bot import BotControl
from client.markups.core import TextMarkup, DataTextWidget
from client.utils import Emoji


class FeedbackMixin:
    _feedback_headers = {
        "default": DataTextWidget(header=f'{Emoji.REPORT} Feedback'),
        "info": DataTextWidget(header=f"{Emoji.INFO} Info"),
        "error": DataTextWidget(header=f"{Emoji.DENIAL} Error"),
    }


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
                chat_id=self._bot_control.user_id,
                message_id=self._bot_control.storage.message_id,
                text=(await self._text_markup.text) + (
                    '\n' + self.feedback.text.as_html() if self.feedback.active else ''),
                reply_markup=await markup.markup
            )
        except TelegramBadRequest:
            pass

        self.feedback.off()
        await self.clean_trash()
        await self.update_interface_in_redis()

    async def handling_unexpected_error(self, response):
        await self.update_feedback('internal server error', type_="error")
        await self.open_session()

        try:
            response_ = await response.json()
            errors.error(
                f"Current markup: {self._current_markup.__class__.__name__}\nDetail: {response_['detail']}\nStatus: {response.status}"
            )
        except (ContentTypeError, Exception):
            errors.error("internal server error")

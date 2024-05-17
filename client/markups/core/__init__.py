from abc import abstractmethod, ABC
from typing import List, Dict

from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import State
from aiogram.types import InlineKeyboardButton
from aiogram.utils.formatting import as_list, Text, Bold, Italic
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup

from client.utils import Emoji


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
    def __init__(self, map_: List[DataTextWidget | TextWidget] = None):
        self._map = map_

    @property
    def map(self):
        return self._map

    @property
    async def text(self):
        if self._map is None:
            return Emoji.BAN
        return (as_list(*[text.text for text in self._map])).as_html()

    def __getitem__(self, index: int):
        return self._map[index]


class MarkupMap:
    def __init__(self, map_: List[List[ButtonWidget]] = None):
        self.map = map_

    @property
    async def markup(self):
        if self.map is None:
            return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=Emoji.BAN)]])

        markup = InlineKeyboardBuilder()
        for buttons_row in self.map:
            row = InlineKeyboardBuilder()
            for button in buttons_row:
                row.button(text=button.text, callback_data=button.callback_data)
            markup.attach(row)
        return markup.as_markup()


class TextMarkup(ABC):
    def __init__(
            self,
            text_map: TextMap = TextMap(),
            markup_map: MarkupMap = MarkupMap(),
            state: State | None = None
    ):
        self.text_map = text_map
        self.markup_map = markup_map
        self.state = state

    @abstractmethod
    async def open(self, **kwargs):
        ...

    @property
    async def text(self):
        return await self.text_map.text

    @property
    async def markup(self):
        return await self.markup_map.markup

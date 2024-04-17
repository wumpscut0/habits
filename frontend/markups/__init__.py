import pickle
from base64 import b64encode
from typing import List, Dict
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InputMediaPhoto
from aiogram.utils.formatting import as_list, Text
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from config import *


class TextWidget:
    def __init__(
            self,
            header: str | Text,
            *,
            data: str | Text = '❔',
            mark: str = '',
    ):
        self._header = header
        self._data = data
        self._mark = mark
        self._default_mark = self._mark
        self._default_data = self._data

    @property
    def text(self):
        separator = '' if self._header.startswith(' ') else ' '
        return Text(self._mark) + Text(separator) + Text(self._header) + Text(': ') + Text(self._data)

    def reset(self):
        self._data = self._default_data
        self._mark = self._default_mark

    async def update_text(
            self,
            *,
            header: str | Text = None,
            data: str | Text = None,
            mark: str = None,
    ):
        if data is not None:
            self._data = data
        if mark is not None:
            self._mark = mark
        if header is not None:
            self._header = header


class ButtonWidget:
    def __init__(
            self,
            text: str,
            callback_data: str | CallbackData,
            mark: str = '',
    ):
        self._text = text
        self._callback_data = callback_data
        self._mark = mark
        self._default_mark = self._mark

    @property
    def button(self):
        separator = '' if self._text.startswith(' ') else ' '
        return InlineKeyboardButton(text=self._mark + separator + self._text, callback_data=self._callback_data)

    def reset(self):
        self._mark = self._default_mark

    async def update_button(
            self,
            text: str = None,
            callback_data: str | CallbackData = None,
            mark: str = None,
    ):
        if text is not None:
            self._text = text
        if callback_data is not None:
            self._callback_data = callback_data
        if mark is not None:
            self._mark = mark


class CommonTexts:
    @staticmethod
    def feedback():
        return TextWidget('📝 Feedback', mark=OK)


class CommonButtons:
    @staticmethod
    def accept(callback_data: str | CallbackData):
        return ButtonWidget('Accept', callback_data, OK)

    @staticmethod
    def left(callback_data: str | CallbackData):
        return ButtonWidget('⬅️', callback_data)

    @staticmethod
    def right(callback_data: str | CallbackData):
        return ButtonWidget('➡️', callback_data)

    @staticmethod
    def back(callback_data: str | CallbackData):
        return ButtonWidget('⬇️', callback_data)


class SerializableMixin:
    async def serialize(self):
        return b64encode(pickle.dumps(self)).decode()


class WithPhotoMixin:
    def __init__(self):
        self._photo: str | InputMediaPhoto | None = None

    @property
    def photo(self):
        return self._photo

    @photo.setter
    def photo(self, photo: str | InputMediaPhoto):
        self._photo = photo


class Markup(SerializableMixin):
    def __init__(self):
        self._header: str | Text = Text()
        self._text_map: Dict[str, TextWidget] = {}
        self._markup_map: List[Dict[str, ButtonWidget]] = [{}]

    @property
    async def text(self):
        return (Text(self._header) + '\n' + as_list(*[row.text for row in self._text_map.values()])).as_html()

    @property
    async def markup(self):
        return InlineKeyboardBuilder([[button.button for button in row.values()] for row in self._markup_map]).as_markup()

    async def _update_header(self, header: str | Text):
        self._header = header




import pickle
from abc import ABC, abstractmethod
from base64 import b64encode
from typing import List, Dict
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import State
from aiogram.types import InputMediaPhoto
from aiogram.utils.formatting import as_list, Text, Bold, Italic
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from config import *
from frontend.FSM import StateManager


class Widget:
    def __init__(self):
        self._status = True

    def on(self):
        self._status = True

    def off(self):
        self._status = False


class TextWidget:
    def __init__(self, text: str):
        self._text = text
        self._default_text = self._text

    def __repr__(self):
        return self.text.as_html()

    @property
    def text(self):
        if self._text and self._status:
            text = Bold(self._text)
        else:
            text = Text('')
        return text

    @text.setter
    def text(self, header):
        self._text = header

    async def reset(self):
        self._text = self._default_text


class DataTextWidget:
    def __init__(
            self,
            header: str,
            *,
            data: str = '❔',
            mark: str = '',
            sep: str = ': '
    ):
        self._header = header
        self._data = data
        self._mark = mark
        self._sep = sep
        self._default_mark = self._mark
        self._default_data = self._data

    def __repr__(self):
        return self.text.as_html()

    @property
    def text(self):
        separator = '' if str(self._header).startswith(' ') else ' '
        return Text(self._mark) + Text(separator) + Bold(self._header) + Text(self._sep) + Italic(self._data)

    @property
    def data(self):
        return self._data

    async def reset(self):
        self._data = self._default_data
        self._mark = self._default_mark

    async def update_text(
            self,
            *,
            header: str = None,
            data: str = None,
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

    async def reset(self):
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
        return DataTextWidget('📝 Feedback')


class CommonButtons:
    @staticmethod
    def accept(callback_data: str | CallbackData, text='Accept'):
        return ButtonWidget(text, callback_data, OK)

    @staticmethod
    def left(callback_data: str | CallbackData, text='Previous'):
        return ButtonWidget(f'⬅️ {text}', callback_data)

    @staticmethod
    def right(callback_data: str | CallbackData, text='Next'):
        return ButtonWidget(f'➡️ {text}', callback_data)

    @staticmethod
    def back(callback_data: str | CallbackData, text='Back'):
        return ButtonWidget(f'⬇️ {text}', callback_data)


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


class Markup(ABC):
    def __init__(self):
        self._init()

    def _init(self):
        self._init_related_markups()
        self._init_state()
        self._init_data()
        self._init_text_map()
        self._init_markup_map()

    def _init_state(self):
        self._state_manager: StateManager = StateManager()

    def _init_related_markups(self):
        ...

    def _init_data(self):
        ...

    @abstractmethod
    def _init_text_map(self):
        self._text_map: Dict[str, DataTextWidget | TextWidget] = {}

    def _init_markup_map(self):
        self._markup_map: List[Dict[str, ButtonWidget]] = [{}]

    @property
    def state(self):
        return self._state_manager.state

    @state.setter
    def state(self, state: State):
        self._state_manager.state = state

    @property
    def text_map(self):
        return self._text_map

    @property
    async def text(self):
        return (as_list(*[row.text for row in self._text_map.values()])).as_html()

    @property
    async def markup(self):
        return InlineKeyboardBuilder([[button.button for button in row.values()] for row in self._markup_map]).as_markup()

    async def reset(self):
        await self._state_manager.reset()
        for widget in self._text_map.values():
            await widget.reset()
        for row in self._markup_map:
            for button in row.values():
                await button.reset()




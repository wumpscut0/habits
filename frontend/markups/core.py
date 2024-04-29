import pickle
from abc import ABC, abstractmethod
from base64 import b64encode
from typing import List, Dict
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InputMediaPhoto
from aiogram.utils.formatting import as_list, Text, Bold, Italic
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from config import *
from frontend.markups import Interface


class Hidden:
    def __init__(self, active=True):
        self._active = active

    def on(self):
        self._active = True

    def off(self):
        self._active = False

    @property
    def active(self):
        return self._active


class TextWidget:
    def __init__(self, text: str):
        super().__init__()
        self._text = text
        self._default_text = self._text

    def __repr__(self):
        return self.text.as_html()

    @property
    def text(self):
        if self._text:
            text = Bold(self._text)
        else:
            text = Text('')
        return text

    @text.setter
    def text(self, header):
        self._text = header

    async def reset(self):
        self._text = self._default_text


class DataTextWidget(Hidden):
    def __init__(
            self,
            header: str,
            *,
            data: str = '❔',
            mark: str = '',
            sep: str = ': ',
            active=True
    ):
        super().__init__(active)
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

    async def reset(self, active=False):
        self._active = active
        self._data = self._default_data
        self._mark = self._default_mark

    async def update_text(
            self,
            *,
            header: str = None,
            data: str = None,
            mark: str = None,
            active=True,
    ):
        self._active = active
        if data is not None:
            self._data = data
        if mark is not None:
            self._mark = mark
        if header is not None:
            self._header = header


class ButtonWidget(Hidden):
    def __init__(
            self,
            text: str,
            callback_data: str | CallbackData,
            *,
            mark: str = '',
            active=True
    ):
        super().__init__(active)
        self._text = text
        self._callback_data = callback_data
        self._mark = mark
        self._default_mark = self._mark

    @property
    def button(self):
        separator = '' if self._text.startswith(' ') else ' '
        return InlineKeyboardButton(text=self._mark + separator + self._text, callback_data=self._callback_data)

    async def reset(self, active=False):
        self._active = active
        self._mark = self._default_mark

    async def update_button(
            self,
            *,
            text: str = None,
            callback_data: str | CallbackData = None,
            mark: str = None,
            active=True,
    ):
        self._active = active
        if text is not None:
            self._text = text
        if callback_data is not None:
            self._callback_data = callback_data
        if mark is not None:
            self._mark = mark


class CommonButtons:
    @staticmethod
    def accept(callback_data: str | CallbackData, text='Accept'):
        return ButtonWidget(text, callback_data, mark=Emoji.OK)

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
    def __init__(self, interface: Interface):
        self._interface = interface
        self._init_state()
        self._init_text_map()
        self._init_markup_map()
        self._base_text_map = {
            "feedback": DataTextWidget('📝 Feedback', active=False)
        }

    def _init_state(self):
        """
        Contract schema: self.state = State
        """
        self.state = None

    @abstractmethod
    def _init_text_map(self):
        """
        Contract schema: self.text_map = Dict[str, DataTextWidget | TextWidget]
        """
        self.text_map: Dict[str, DataTextWidget | TextWidget] = {}

    def _init_markup_map(self):
        """
        Contract schema: self.markup_map = List[Dict[str, ButtonWidget]]
        """
        self.markup_map: List[Dict[str, ButtonWidget]] = [{}]

    async def open(self, state):
        await self._interface.update(state, self)
        await self._base_text_map['feedback'].reset()

    async def update_feedback(self, data: str):
        await self._base_text_map['feedback'].update_text(data=data)

    @property
    async def text(self):
        self.text_map.update(self._base_text_map)
        return (as_list(*[row.text for row in self.text_map.values() if row.active])).as_html()

    @property
    async def markup(self):
        return InlineKeyboardBuilder([[button.button for button in row.values() if button.active] for row in self.markup_map]).as_markup()
    
    async def reset_text(self, active=False):
        for widget in self.text_map.values():
            await widget.reset(active)
            
    async def reset_markup(self, active=False):
        for row in self.markup_map:
            for button in row.values():
                await button.reset(active)
    
    async def reset_all(self, active=False):
        await self.reset_text(active)
        await self.reset_markup(active)

    async def abort_session(self, state):
        self._interface.title_screen.open(state)

    async def handling_unexpected_error(self, state):
        await self.update_feedback('Internal server error.')
        await self.open(state)


# class Markup(ABC):
#     def __init__(self):
#         self._init()
#         self._state = None
#
#     def _init(self):
#         self._init_state()
#         self._inittext_map()
#         self._initmarkup_map()
#
#     def _init_state(self):
#         self._state = None
#
#     @abstractmethod
#     def _inittext_map(self):
#         self.text_map: Dict[str, DataTextWidget | TextWidget] = {}
#
#     def _initmarkup_map(self):
#         self.markup_map: List[Dict[str, ButtonWidget]] = [{}]
#
#     @property
#     def state(self):
#         return self._state
#
#     @state.setter
#     def state(self, state: State):
#         self._state = state
#
#     @property
#     def text_map(self):
#         return self.text_map
#
#     @property
#     def markup_map(self):
#         return self.markup_map
#
#     @property
#     async def text(self):
#         return (as_list(*[row.text for row in self.text_map.values() if row.active])).as_html()
#
#     @property
#     async def markup(self):
#         return InlineKeyboardBuilder([[button.button for button in row.values() if button.active] for row in self.markup_map]).as_markup()
#
#     async def reset(self):
#         for widget in self.text_map.values():
#             await widget.reset()
#         for row in self.markup_map:
#             for button in row.values():
#                 await button.reset()


# class TextMap(ABC):
#     def __init__(self):
#         self.text_map = None
#
#
#     @property
#     async def text(self):
#         return (as_list(*[widget.text for widget in vars(self).values() if not callable(widget) and widget.active])).as_html()

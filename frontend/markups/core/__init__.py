import pickle
from base64 import b64encode
from typing import List, Dict, Any

from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import State
from aiogram.types import InputMediaPhoto
from aiogram.utils.formatting import as_list, Text, Bold, Italic
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

from frontend.controller import Interface
from frontend.markups import Emoji


class Hideable:
    def __init__(self, active=True):
        self._active = active

    def on(self):
        self._active = True

    def off(self):
        self._active = False

    @property
    def active(self):
        return self._active


class Resettable:
    def __init__(self, obj: Any):
        self.obj = obj
        self._default_attrs = {name: value for name, value in vars(self.obj).items() if not callable(value)}

    async def reset(self):
        for name, value in self._default_attrs.items():
            setattr(self.obj, name, value)


class TextWidget(Resettable, Hideable):
    def __init__(self, text: str = None, active=True):
        super(Hideable, self).__init__(active)
        self._text = text
        self._default_text = self._text

    def __repr__(self):
        return self._text

    @property
    def text(self):
        if self._text is None:
            return Text(Emoji.BAN)
        return Bold(self._text)

    @text.setter
    def text(self, text):
        self._text = text


class DataTextWidget(Hideable, Resettable):
    def __init__(
            self,
            header: str,
            *,
            data: str = Emoji.GREY_QUESTION,
            mark: str = '',
            sep: str = ': ',
            end: str = '',
            active=True
    ):
        super(Hideable, self).__init__(active)
        self.header = header
        self.data = data
        self.mark = mark
        self.sep = sep
        self.end = end
        super(Resettable, self).__init__(self)

    def __repr__(self):
        return self.text.as_html()

    @property
    def text(self):
        separator = '' if str(self.header).startswith(' ') else ' '
        return Text(self.mark) + Text(separator) + Bold(self.header) + Text(self.sep) + Italic(self.data) + Italic(self.end)


class ButtonWidget(Hideable, Resettable):
    def __init__(
            self,
            text: str,
            callback_data: str | CallbackData,
            *,
            mark: str = '',
            active=True
    ):
        super(Hideable, self).__init__(active)
        self.text = text
        self.callback_data = callback_data
        self.mark = mark
        super(Resettable, self).__init__(self)

    @property
    def button(self):
        separator = '' if self.text.startswith(' ') else ' '
        return InlineKeyboardButton(text=self.mark + separator + self.text, callback_data=self.callback_data)


class SerializableMixin:
    async def serialize(self):
        return b64encode(pickle.dumps(self)).decode()


class PhotoMarkup:
    def __init__(self):
        self._photo: str | InputMediaPhoto | None = None

    @property
    def photo(self):
        return self._photo

    @photo.setter
    def photo(self, photo: str | InputMediaPhoto):
        self._photo = photo


class TextMap:
    def __init__(self, map_: Dict[str, DataTextWidget | TextWidget] = None):
        self._map = map_

    @property
    async def text(self):
        if self._map is None:
            return f'{Emoji.BAN}'
        return (as_list(*[row.text for row in self._map.values() if row.active])).as_html()

    def __getitem__(self, name):
        return self._map[name]

    async def reset(self):
        for widget in self._map.values():
            await widget.reset()


class MarkupMap:
    def __init__(self, map_: List[Dict[str, ButtonWidget]] = None):
        self._map = map_
        self._adapt_map = {name: button for row in map_ for name, button in row.items()}

    @property
    async def markup(self):
        return InlineKeyboardBuilder(
            [[button.button for button in row.values() if button.active] for row in self._map]
        ).as_markup()

    def __getitem__(self, name):
        return self._adapt_map[name]

    async def set_map(self, map_: List[Dict[str, ButtonWidget]]):
        self._map = map_

    async def reset(self):
        for button in self._adapt_map.values():
            await button.reset()


class TextMarkup:
    def __init__(
            self,
            interface: Interface,
            *,
            text_map: TextMap = TextMap(),
            markup_map: MarkupMap = MarkupMap(),
            state: State | None = None
    ):
        self._interface = interface
        self.text_map = text_map
        self.markup_map = markup_map
        self.state = state

    async def open(self, state):
        await self._interface.update(state, self)

    @property
    async def text(self):
        return self.text_map.text

    @property
    async def markup(self):
        if self.markup_map.markup is not None:
            return self.markup_map.markup

    async def reset(self):
        await self.text_map.reset()
        if self.markup_map is not None:
            await self.markup_map.reset()

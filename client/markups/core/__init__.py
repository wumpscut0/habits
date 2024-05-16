from typing import List, Dict

from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import State
from aiogram.utils.formatting import as_list, Text, Bold, Italic
from aiogram.utils.keyboard import InlineKeyboardBuilder

from client.utils import Emoji


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


# class Resettable:
#     def __init__(self, obj: Any):
#         self.obj = obj
#         self._default_attrs = {name: value for name, value in vars(self.obj).items() if not callable(value)}
#
#     async def reset(self):
#         for name, value in self._default_attrs.items():
#             setattr(self.obj, name, value)


class TextWidget(Hideable):
    def __init__(self, text: str = None, active=True):
        super().__init__(active)
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


class DataTextWidget(Hideable):
    def __init__(
            self,
            *,
            header: str = None,
            data: str = Emoji.GREY_QUESTION,
            mark: str = '',
            sep: str = ': ',
            end: str = '',
            active=True
    ):
        super().__init__(active)
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


class ButtonWidget(Hideable):
    def __init__(
            self,
            *,
            text: str = None,
            callback_data: str | CallbackData = None,
            mark: str = '',
            active=True
    ):
        super().__init__(active)
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
    def __init__(self, map_: Dict[str, DataTextWidget | TextWidget]):
        self._map = map_

    @property
    async def text(self):
        return (as_list(*[text.text for text in self._map.values() if text.active])).as_html()

    def __getitem__(self, name):
        return self._map[name]


class MarkupMap:
    def __init__(self, map_: List[Dict[str, ButtonWidget]] = None):
        if map_ is None:
            self._map = []
            self._adapt_map = {}
        else:
            self._map = map_
            self._adapt_map = {name: button for row in map_ for name, button in row.items()}

    @property
    async def markup(self):
        markup = InlineKeyboardBuilder()
        for row in self._map:
            markup_part = InlineKeyboardBuilder()
            for button in row.values():
                if button.active:
                    markup_part.button(text=button.text, callback_data=button.callback_data)
            markup.attach(markup_part)
        return markup.as_markup()

    def __getitem__(self, name):
        return self._adapt_map[name]

    async def add_buttons(self, map_: Dict[str, ButtonWidget]):
        self._map.append(map_)
        for name, button in map_.items():
            self._adapt_map[name] = button


class TextMarkup:
    def __init__(
            self,
            text_map: TextMap,
            markup_map: MarkupMap = MarkupMap(),
            state: State | None = None
    ):
        self.text_map = text_map
        self.markup_map = markup_map
        self.state = state

    async def open(self):
        trash =
        for message_id in self._interface.storage.trash:
            await self.delete_message(message_id)
        storage.delete(f"trash:{self.chat_id}")
        message_id = storage.get(f"{self.chat_id}")
        await self.state.set_state(markup.state)
        try:
            await bot.edit_message_text(
                chat_id=self.chat_id,
                message_id=message_id,
                text=(await markup.text) + ('\n' + self.feedback.text.as_html() if self.feedback.active else ''),
                reply_markup=await markup.markup
            )
        except TelegramBadRequest:
            pass

    @property
    async def text(self):
        return await self.text_map.text

    @property
    async def markup(self):
        if await self.markup_map.markup is not None:
            return await self.markup_map.markup

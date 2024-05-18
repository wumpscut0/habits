from typing import List

from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import State

from aiogram.types import InputMediaPhoto
from aiogram.utils.formatting import as_list, Text, Bold, Italic
from aiogram.utils.keyboard import InlineKeyboardBuilder

from client.utils import Emoji


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


class TextMap:
    def __init__(self, map_: List[DataTextWidget | TextWidget] | None = None):
        super().__init__()
        self._text_map = [] if map_ is None else map_

    def set_text_map(self, map_: List[DataTextWidget | TextWidget]):
        self._text_map = map_

    def add_text_row(self, text: DataTextWidget | TextWidget):
        self._text_map.append(text)

    @property
    def text(self):
        if not self._text_map:
            return Emoji.BAN
        return (as_list(*[text.text for text in self._text_map])).as_html()


class MarkupMap:
    """
    Max telegram inline keyboard buttons row is 8.
     add_button_in_last_row will automatically move the button to the new row
    """
    _limitation_row = 8

    def __init__(self, map_: List[List[ButtonWidget]] | None = None):
        super().__init__()
        self._markup_map = [[]] if map_ is None else map_

    def set_markup_map(self, map_: List[List[ButtonWidget]]):
        self._markup_map = map_

    def add_button_in_last_row(self, button: ButtonWidget):
        if len(self._markup_map[-1]) == self._limitation_row:
            self.add_button_in_new_row(button)
        else:
            self._markup_map[-1].append(button)

    def add_button_in_new_row(self, button: ButtonWidget):
        self._markup_map.append([button])

    @property
    def markup(self):
        if self._markup_map == [[]]:
            return

        markup = InlineKeyboardBuilder()
        for buttons_row in self._markup_map:
            row = InlineKeyboardBuilder()
            for button in buttons_row:
                row.button(text=button.text, callback_data=button.callback_data)
            markup.attach(row)
        return markup.as_markup()


class TextMessage(TextMap, MarkupMap):
    def __init__(self, state: State | None = None):
        super().__init__()
        self.state = state


class PhotoMessage(TextMessage):
    def __init__(self, photo: str | InputMediaPhoto):
        super().__init__()
        self.photo = photo

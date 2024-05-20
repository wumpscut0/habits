from abc import abstractmethod, ABC
from typing import List

from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import State

from aiogram.types import InputMediaPhoto
from aiogram.utils.formatting import as_list, Text, Bold, Italic
from aiogram.utils.keyboard import InlineKeyboardBuilder

from client.api import ServerApi
from client.utils import Emoji


class InitializeMarkupInterface(ABC):
    api = ServerApi()

    @abstractmethod
    def __init__(self, state: State | None = None):
        self.text_message_markup = TextMessageMarkup(state)
        """
        super().__init__()
        `self.<widget_name> = TextWidget("hello"),`
        """
        ...

    @abstractmethod
    async def init(self, *args, **kwargs):
        """
        self.text_message.add_text_row(self.<widget_name>)\n
        return self.text_message
        """
        ...


class TextWidget:
    def __init__(
            self,
            *,
            mark: str = '',
            text: str = None,

    ):
        self.mark = mark
        self._text = text

    def __repr__(self):
        return self._text

    @property
    def text(self):
        if self._text is None:
            return Text(Emoji.BAN)
        separator = '' if str(self._text).startswith(' ') else ' '
        return Text(self.mark) + Text(separator) + Bold(self._text)

    @text.setter
    def text(self, value):
        self._text = value


class DataTextWidget(TextWidget):
    def __init__(
            self,
            *,
            mark: str = '',
            text: str = None,
            data: str = Emoji.GREY_QUESTION,
            sep: str = ': ',
            end: str = '',
    ):
        super().__init__(
            mark=mark,
            text=text,
        )
        self.data = data
        self.sep = sep
        self.end = end

    def text(self):
        return super().text + Text(self.sep) + Italic(self.data) + Italic(self.end)


class ButtonWidget(TextWidget):
    def __init__(
            self, *,
            mark: str = '',
            text: str = None,
            callback_data: str | CallbackData = None
    ):
        super().__init__(
            mark=mark,
            text=text,
        )
        self._callback_data = callback_data


    @property
    def callback_data(self):
        if not self._callback_data:
            return Emoji.BAN
        return self._callback_data

    @callback_data.setter
    def callback_data(self, callback_data):
        self._callback_data = callback_data


class TextMarkup:
    def __init__(self, map_: List[DataTextWidget | TextWidget] | None = None):
        super().__init__()
        self._text_map = [] if map_ is None else map_

    @property
    def text_map(self):
        return self._text_map

    def set_text_map(self, map_: List[DataTextWidget | TextWidget]):
        self._text_map = map_

    def add_text_row(self, text: DataTextWidget | TextWidget):
        self._text_map.append(text)

    def add_texts_rows(self, *args: DataTextWidget | TextWidget):
        for text in args:
            self._text_map.append(text)

    @property
    def text(self):
        if not self._text_map:
            return Emoji.BAN
        return (as_list(*[text.text for text in self._text_map])).as_html()


class KeyboardMarkup:
    """
    Max telegram inline keyboard buttons row is 8.
     add_button(s)_in_last_row will automatically move the button to the new row
    """
    _limitation_row = 8

    def __init__(self, map_: List[List[ButtonWidget]] | None = None):
        super().__init__()
        self._keyboard_map = [[]] if map_ is None else map_

    @property
    def keyboard_map(self):
        return self._keyboard_map

    def set_markup_map(self, map_: List[List[ButtonWidget]]):
        self._keyboard_map = map_

    def add_button_in_last_row(self, button: ButtonWidget):
        if len(self._keyboard_map[-1]) == self._limitation_row:
            self.add_button_in_new_row(button)
        else:
            self._keyboard_map[-1].append(button)

    def add_buttons_in_last_row(self, *args: ButtonWidget):
        for button in args:
            self.add_button_in_last_row(button)

    def add_button_in_new_row(self, button: ButtonWidget):
        self._keyboard_map.append([button])

    def add_buttons_in_new_row(self, *args: ButtonWidget):
        self._keyboard_map.append([])
        limit = 0
        for button in args:
            if limit == self._limitation_row:
                limit = 0
                self.add_button_in_new_row(button)
            else:
                self.add_button_in_last_row(button)
            limit += 1

    @property
    def keyboard(self):
        if self._keyboard_map == [[]]:
            return

        markup = InlineKeyboardBuilder()
        for buttons_row in self._keyboard_map:
            row = InlineKeyboardBuilder()
            for button in buttons_row:
                row.button(text=button.text, callback_data=button.callback_data)
            markup.attach(row)
        return markup.as_markup()


class TextMessageMarkup(TextMarkup, KeyboardMarkup):
    def __init__(self, state: State | None = None):
        super().__init__()
        self.state = state

    def __add__(self, text_message_markup):
        if not isinstance(text_message_markup, TextMessageMarkup):
            raise ValueError("TextMessageMarkup can only concatenate with TextMessageMarkup")
        for text_row in text_message_markup.text_map:
            self.add_text_row(text_row)
        for buttons_row in text_message_markup.keyboard_map:
            self.add_buttons_in_new_row(*buttons_row)


class PhotoMessageMarkup(TextMessageMarkup):
    def __init__(self, photo: str | InputMediaPhoto):
        super().__init__()
        self.photo = photo

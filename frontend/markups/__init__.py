import pickle
from base64 import b64encode
from typing import List, Dict
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InputMediaPhoto
from aiogram.utils.formatting import as_list, Text
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton


class SerializableMixin:
    async def serialize(self):
        return b64encode(pickle.dumps(self)).decode()


class Markup(SerializableMixin):
    def __init__(self):
        self._photo: str | InputMediaPhoto | None = None
        self._header: str | Text = Text()

        self._text_map: List[Dict[str, str | Text]] = [{"mark": "", "header": "", "data": ""}]

        self._markup_map: List[List[Dict[str, str | CallbackData]]] = [[]]

    @property
    def photo(self):
        return self._photo

    @photo.setter
    def photo(self, photo: str | InputMediaPhoto):
        self._photo = photo

    @property
    async def text(self):
        return ((Text(self._header) + '\n' + as_list(*[Text(row['mark']) + Text(row['header']) + Text(row['data']) for row in self._text_map]))
                .as_html())

    @property
    async def markup(self):
        return InlineKeyboardBuilder([[InlineKeyboardButton(
            text=button["mark"] + button['text'],
            callback_data=button['callback_data']
        ) for button in row] for row in self._markup_map]).as_markup()

    async def _update_header(self, header: str | Text):
        self._header = header

    async def _update_text(self, update_map: Dict[int, Dict[str, str | Text]]):
        """
        Declarative updating
        :param update_map: Dict[WHERE?, Dict[WHAT?, DATA]]
        :return:
        """
        for row_number, row_map in update_map.items():
            self._text_map[row_number].update(row_map)

    async def _update_markup(self, update_map: Dict[int, Dict[int, Dict[str, str | CallbackData]]]):
        """
        Declarative updating
        :param update_map: Dict[WHERE?, Dict[WHERE?, Dict[WHAT?, DATA]]]
        :return:
        """
        for row_number, row_map in update_map.items():
            for button_number, button_data in row_map.items():
                self._markup_map[row_number][button_number].update(button_data)











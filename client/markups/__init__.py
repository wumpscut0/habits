from abc import abstractmethod, ABC

from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import State

from client.api import Api
from client.bot.FSM import States
from client.markups.core import TextMessageMarkup, ButtonWidget, TextWidget
from client.utils import Emoji


class InitializeMarkupInterface(ABC):
    @abstractmethod
    def __init__(self, state: State | None = None):
        self.text_message_markup = TextMessageMarkup(state)
        """
        super().__init__()
        `self.<widget_name> = <widget_class>(text="hello"),`
        """
        ...


class InitializeApiMarkupInterface(InitializeMarkupInterface):
    _api = Api()

    @abstractmethod
    async def init(self, *args, **kwargs):
        """
        self.text_message.add_text_row(self.<widget_name>)\n
        return self.text_message
        """
        ...


class Info(InitializeMarkupInterface):
    def __init__(self, info: str, button_text="Ok", callback_data="return_to_context"):
        super().__init__()
        self._info = TextWidget(text=info)
        self._ok = ButtonWidget(text=button_text, callback_data=callback_data)
        self.text_message_markup.add_text_row(self._info)
        self.text_message_markup.add_button_in_last_row(self._ok)


class Temp(InitializeMarkupInterface):
    def __init__(self):
        super().__init__()
        self.temp = TextWidget(text=f"{Emoji.HOURGLASS_START} Processing...")
        self.text_message_markup.add_text_row(self.temp)


class Back(InitializeMarkupInterface):
    def __init__(self, *, callback_data: str | CallbackData = "return_to_context", mark=f"{Emoji.BACK}", text="Back"):
        super().__init__()
        self.back = ButtonWidget(mark=mark, text=text, callback_data=callback_data)
        self.text_message_markup.add_button_in_new_row(self.back)


class Pagination(InitializeMarkupInterface):
    def __init__(
        self,
        left_callback_data: str | CallbackData,
        right_callback_data: str | CallbackData,
        left_mark: str = "",
        right_mark: str = ""

    ):
        super().__init__()
        self.left = ButtonWidget(text=f"{Emoji.LEFT}", mark=left_mark, callback_data=left_callback_data)
        self.right = ButtonWidget(text=f"{Emoji.RIGHT}", mark=right_mark, callback_data=right_callback_data)
        self.text_message_markup.add_buttons_in_last_row(self.left, self.right)


class LeftBackRight(InitializeMarkupInterface):
    def __init__(
        self,
        back_callback_data: str | CallbackData,
        left_callback_data: str | CallbackData,
        right_callback_data: str | CallbackData,
        left_mark: str = "",
        right_mark: str = ""
    ):
        super().__init__()
        pagination = Pagination(
            left_callback_data=left_callback_data,
            right_callback_data=right_callback_data,
            left_mark=left_mark,
            right_mark=right_mark
        )
        back = Back(callback_data=back_callback_data)
        self.text_message_markup.add_buttons_in_new_row(
            pagination.left,
            back.back,
            pagination.right,
        )


class Input(InitializeMarkupInterface):
    def __init__(
            self,
            info_text: str,
            *,
            info_mark: str = "",
            back_mark: str = f"{Emoji.DENIAL}",
            back_callback_data: str = "return_to_context",
            back_text: str = "Cancel",
            state: States | None = None
    ):
        super().__init__(state)
        self.info = TextWidget(mark=info_mark, text=info_text)
        self.text_message_markup.add_text_row(self.info)
        self.text_message_markup += Back(mark=back_mark, text=back_text, callback_data=back_callback_data).text_message_markup


class Conform(InitializeMarkupInterface):
    def __init__(
            self,
            info: str,
            yes_callback_data: str | CallbackData,
            yes_mark: str = Emoji.OK,
            yes_text: str = f"Yes",
            no_mark: str = Emoji.DENIAL,
            no_text: str = f"No",
            no_callback_data: str | CallbackData = "return_to_context"
    ):
        super().__init__()
        self.yes = ButtonWidget(mark=yes_mark, text=yes_text, callback_data=yes_callback_data)
        self.no = ButtonWidget(mark=no_mark, text=no_text, callback_data=no_callback_data)
        self.text_message_markup.add_text_row(TextWidget(text=info))
        self.text_message_markup.add_buttons_in_new_row(self.yes, self.no)

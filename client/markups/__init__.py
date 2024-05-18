from abc import ABC, abstractmethod

from client.api import ServerApi
from client.markups.core import TextMap, TextWidget, MarkupMap, ButtonWidget, DataTextWidget, TextMessage

from client.utils import Emoji


class MarkupInitializeInterface(ABC):
    api = ServerApi()

    def __init__(self):
        super().__init__()
        self._info_feedback = DataTextWidget(header=f"{Emoji.INFO} Info"),
        self._error_feedback = DataTextWidget(header=f"{Emoji.DENIAL} Error"),

    @abstractmethod
    async def init(self, *args, **kwargs):
        ...


class Info(ABC):
    def __init__(self):
        super().__init__()
        self._ok = ButtonWidget(text=f"{Emoji.OK} Ok")

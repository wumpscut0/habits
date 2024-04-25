from config import Emoji
from frontend.markups import Markup, TextWidget, ButtonWidget
from frontend.markups.interface import Interface


class SignIn(Markup):
    def __init__(self, interface: Interface):
        super().__init__()
        self.interface = interface

    def _init_text_map(self):
        self._text_map = {
            "info": TextWidget(f"{Emoji.BRAIN} Psychological service")
        }

    def _init_markup_map(self):
        self._markup_map = [
            {
                "sign_in": ButtonWidget(f'{Emoji.DOOR}', 'try_profile'),
                "notifications": ButtonWidget(f"{Emoji.MEGAPHONE}", "invert notifications")
            }
        ]

    def invert_notifications(self):
        self._markup_map[0]['notifications'].update_button()

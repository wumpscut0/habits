import re

from config import MAX_NAME_LENGTH
from frontend.markups import *


class Habits(Markup):
    def __init__(self, interface: Interface):
        super().__init__()
        self._interface = interface
        self._habits = []

    def _init_text_map(self):
        self._text_map = {
            "total_completed": DataTextWidget('Total fixed habits', data='0'),
            "feedback": CommonTexts.feedback(),
        }

    def _init_markup_map(self):
        self._markup_map = [
            {
                "show_up": ButtonWidget(f"{Emoji.EYE} Show up targets", "show_habits"),
                "create": ButtonWidget(f"{Emoji.TARGET} Create new target", "create_habit"),
                "show_completed": ButtonWidget(f"{Emoji.SHINE_STAR} Show completed targets", "show_completed_habits")
            },
            {
                "update": ButtonWidget(f"{Emoji.CYCLE} Update target", "update_habit"),
                "delete": ButtonWidget(f"{Emoji.DENIAL} Delete target", "delete_habit"),
            },
        ]

    async def open_habits(self, session: ClientSession, state: FSMContext):
        async with session.get('/show_up') as response:
            if not (await response.json())['habits']:
                self._text_map['feedback'].update_text(data='No current targets so far.')


class CreateHabit(Markup):
    def __init__(self, interface: Interface):
        super().__init__(interface)
        self.name = None

    def _init_state(self):
        self._state = States.input_habit_name

    def _init_text_map(self):
        self._text_map = {
            "action": TextWidget(f"{Emoji.BULB} Enter the target name"),
            "feedback": CommonTexts.feedback(),
        }

    def _init_markup_map(self):
        self._markup_map = [
            {
                "back": CommonButtons.back("profile", text=f"{Emoji.DENIAL} Cancel")
            }
        ]

    async def input_name(self, name, state):
        if len(name) > MAX_NAME_LENGTH:
            self._text_map['feedback'].update_text(data=f"Maximum name length is {MAX_NAME_LENGTH} simbols")
            await self._interface.update(state, self)
        elif not re.fullmatch(r'[\w\s]+', name, flags=re.I):
            self._text_map['feedback'].update_text(data=f"Name must contains only latin symbols or _ or spaces or digits")
            await self._interface.update(state, self)
        else:
            await self._text_map['feedback'].reset()
            await self._interface.update()

class Habit(Markup):
    def __init__(self):
        super().__init__()

    def _init_text_map(self):
        self._text_map = {
            ""
        }

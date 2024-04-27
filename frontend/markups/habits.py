from frontend.markups import *


class Habits(Markup):
    def __init__(self, interface: Interface):
        super().__init__()
        self._interface = interface
        self._habits = []

    def _init_text_map(self):
        self._text_map = {
            "total_completed": DataTextWidget('Total fixed habits', data='0')
        }

    def _init_markup_map(self):
        self._markup_map = [
            {
                "show_up": ButtonWidget(f"{Emoji.EYE} Show up targets", "show_habits"),
                "create": ButtonWidget(f"{Emoji.TARGET} Create new target", "create_habit"),
            },
            {
                "update": ButtonWidget(f"{Emoji.CYCLE} Update target", "update_habit"),
                "delete": ButtonWidget(f"{Emoji.DENIAL} Delete target", "delete_habit"),
            },
        ]

    async def show_up(self, session: ClientSession, state: FSMContext):
        async with session.get('/')


class Habit(Markup):
    def __init__(self):
        super().__init__()

    def _init_text_map(self):
        self._text_map = {
            ""
        }

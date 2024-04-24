from frontend.markups import Markup, DataTextWidget, ButtonWidget


class Habits(Markup):
    def __init__(self):
        super().__init__()

    def _init_related_markups(self):
        self._habits = []

    def _init_text_map(self):
        self._text_map = {
            "total_completed": DataTextWidget('Total fixed habits', data='0')
        }

    def _init_markup_map(self):
        self._markup_map = [
            {
                "create": ButtonWidget("🧠 Create new target", "create_habit"),
                "update": ButtonWidget("")
            }
        ]

class Habit(Markup):
    def __init__(self):
        super().__init__()


    def _init_text_map(self):


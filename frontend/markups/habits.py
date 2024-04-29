import re
from config import MAX_NAME_LENGTH
from frontend.markups import *


class Habits(Markup):
    def __init__(self, interface: Interface):
        super().__init__(interface)
        self._habits = []

    def _init_text_map(self):
        self.text_map = {
            "total_completed": DataTextWidget('Total fixed habits', data='0'),
        }

    def _init_markup_map(self):
        self.markup_map = [
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
            habits_ = (await response.json())['habits']
            if not habits_:
                await self.update_feedback('No current targets so far.')
                await self.open(state)
            else:


    async def create_habit(self, session, state):
        name = self._interface.input_habit_name
        async with session.post('/create_habit', json={
            "name": name,
            "border": self._interface.input_habit_border.habit_border
        }) as response:
            if response.status == 200:
                await self.update_feedback(f'Habit with name {name} created')
                await self.open(state)
            elif response.status == 401:
                await self.abort_session(state)
            else:
                await self.handling_unexpected_error(state)


class Habit(Markup):
    def __init__(self, interface: Interface):
        super().__init__(interface)

    def _init_text_map(self):
        self.text_map = {
            "name": DataTextWidget('Name'),
            "description": DataTextWidget('Description')
        }

    def _init_markup_map(self):
        self.markup_map = [
            {
                "update_name": ButtonWidget('Update name', "update_habit_name"),
                "update_description": ButtonWidget('Update description', 'update_habit_description'),
                "delete_habit": ButtonWidget('Delete', 'delete_habit')
            }
        ]

    async def load_habits(self):



class InputHabitName(Markup):
    def __init__(self, interface: Interface):
        super().__init__(interface)
        self.name = None

    def _init_state(self):
        self._state = States.input_habit_name

    def _init_text_map(self):
        self.text_map = {
            "action": TextWidget(f"{Emoji.BULB} Enter the target name"),
        }

    def _init_markup_map(self):
        self.markup_map = [
            {
                "back": ButtonWidget(f"{Emoji.DENIAL} Cancel", "profile")
            }
        ]

    async def input_name(self, session: ClientSession, name, state):
        if len(name) > MAX_NAME_LENGTH:
            await self.update_feedback(f"Maximum name length is {MAX_NAME_LENGTH} simbols")
            await self.open(state)
        elif not re.fullmatch(r'[\w\s]+', name, flags=re.I):
            await self.update_feedback(f"Name must contains only latin symbols or _ or spaces or digits")
            await self.open(state)
        else:
            async with session.get(f'/is_name_using?name={name}') as session:
                if session.status == 409:
                    await self.update_feedback((await session.json())['detail'])
                    await self.open(state)
                elif session.status == 401:
                    await self.abort_session(state)
                elif session.status == 200:
                    await self._interface.input_habit_border.open(state)
                else:
                    await self.handling_unexpected_error(state)


class InputHabitBorder(Markup):
    def __init__(self, interface: Interface):
        super().__init__(interface)
        self.habit_border = None

    def _init_state(self):
        self.state = States.input_habit_border

    def _init_text_map(self):
        self.text_map = {
            "action": TextWidget('Enter habit border at 1 to 999\n'
                                 '(By default border is 21 days. This value is standard for fixation habit)')
        }

    def _init_markup_map(self):
        self.markup_map = [
            {
                "skip": ButtonWidget(f'{Emoji.SKIP} Skip', "create_habit")
            }
        ]

    def __call__(self, border: str, state: FSMContext, session: ClientSession):
        if not re.fullmatch(r'\d{1,3}', border):
            self.update_feedback('Border value must be integer and at 1 to 999')
            self.open(state)
        else:
            self.habit_border = int(border)
            self._interface.habits.create_habit(session, border)

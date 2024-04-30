import re
from aiogram.filters.callback_data import CallbackData
from config import MAX_NAME_LENGTH, MAX_DESCRIPTION_LENGTH
from frontend.markups import *


class ShowHabitCallbackData(CallbackData, prefix='show_habit'):
    id: int


class UpdateHabitNameCallbackData(CallbackData, prefix='update_habit_name'):
    id: int


class UpdateHabitDescriptionCallbackData(CallbackData, prefix='update_habit_description'):
    id: int


class DeleteHabitCallbackData(CallbackData, prefix='delete_habit'):
    id: int


class ConformDeleteHabitCallbackData(CallbackData, prefix='conform_delete_habit'):
    id: int


class InvertCompletedHabitCallbackData(CallbackData, prefix='invert_completed_habit'):
    id: int


class HabitManager(Markup):
    def __init__(self, interface: Interface):
        super().__init__(interface)

    def _init_text_map(self):
        self.text_map = {
            "total_completed": DataTextWidget('Total completed habits'),
        }

    def _init_markup_map(self):
        self.markup_map = [
            {
                "habits": ButtonWidget(f"{Emoji.DIAGRAM} Show up current targets", "current_habits"),
                "create_habit": ButtonWidget(f'{Emoji.SPROUT} Create new target', 'create_habit'),
                "show_completed": ButtonWidget(f"{Emoji.SHINE_STAR} Show completed targets", "show_completed_habits"),
            },
        ]

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

    async def delete_habit(self, habit_id, session: ClientSession, state: FSMContext):
        async with session.delete(f'/delete_habit/{habit_id}') as response:
            if response.status == 200:
                await self.update_feedback(f'Habit with name {self._interface.show_up_habits_temp.habits[habit_id]["name"]} created')
                await self._interface.show_up_habits_temp()
            elif response.status == 401:
                await self.abort_session(state)
            else:
                await self.handling_unexpected_error(state)

# id = Column(Integer, primary_key=True)
# name = Column(VARCHAR(MAX_NAME_LENGTH), nullable=False)
# description = Column(VARCHAR(MAX_DESCRIPTION_LENGTH), default='No description')
# completed = Column(Boolean, default=False)
# progress = Column(Integer, default=0)
# border_progress = Column(Integer, default=21)
#
# user_id = Column(Integer, ForeignKey('user.telegram_id'), nullable=False)


class ShowUpHabitsTemp(Markup):
    def __init__(self, interface: Interface):
        super().__init__(interface)
        self.habits = {}

    def _init_text_map(self):
        self.text_map = {
            "info": DataTextWidget(f'{Emoji.DIAGRAM} Marked targets today')
        }

    async def __call__(self, session: ClientSession, state: FSMContext):
        self.markup_map = []
        async with session.get('/show_up_habits') as response:
            if response.status == 200:
                habits_ = await response.json()
                total_completed = 0
                total_targets = len(habits_)

                for habit in habits_:
                    if habit.completed:
                        total_completed += 1
                        self.markup_map.append({
                            habit.id: ButtonWidget(habit.name, ShowHabitCallbackData(id=habit.id), mark=Emoji.OK)
                        })
                    else:
                        self.markup_map.append({
                            habit.id: ButtonWidget(habit.name, ShowHabitCallbackData(id=habit.id))
                        })

                    self.habits[habit.id] = habit

                await self.text_map['info'].update_text(data=f'{total_completed}/{total_targets}')
                await self.open(state)
            elif response.status == 401:
                await self.abort_session(state)
            else:
                await self.handling_unexpected_error(state)


class HabitControlTemp(Markup):
    def __init__(self, interface: Interface):
        super().__init__(interface)

    def _init_text_map(self):
        self.text_map = {
            "name": DataTextWidget('Name'),
            "description": DataTextWidget('Description'),
            "percent_progress": DataTextWidget('Progress'),
            "completed": DataTextWidget('Completed')
        }

    async def show_up(self, id_: int, state: FSMContext):
        habit = self._interface.show_up_habits_temp.habits[id_]

        await self.text_map['name'].update_text(data=habit.name)

        if habit.description is None:
            self.text_map['description'].off()
        else:
            await self.text_map['description'].update_text(data=habit.description)

        await self.text_map['completed'].update_text(data=Emoji.OK if habit.completed else Emoji.DENIAL)

        self.markup_map = [
            {
                "update_name": ButtonWidget('Update name', UpdateHabitNameCallbackData(id=habit.id)),
                "update_description": ButtonWidget('Update description', UpdateHabitDescriptionCallbackData(id=habit.id)),
                "delete_habit": ButtonWidget('Delete', DeleteHabitCallbackData(id=habit.id)),
                "completed": ButtonWidget(f'{Emoji.DENIAL} Incomplete' if habit.completed else f'{Emoji.OK} Complete', InvertCompletedHabitCallbackData(id=habit.id))
            }
        ]
        await self.open(state)

    async def invert_complete(self, id_: int, session: ClientSession, state: FSMContext):
        async with session.patch(f'/invert_habit_completed/{id_}') as response:
            if response.status == 200:
                response = await response.text()
                await self.markup_map[0]['completed'].update_button(text=f'{Emoji.DENIAL} Incomplete' if response == '1' else f'{Emoji.OK} Complete')
                await self.open(state)
            elif response.status == 401:
                await self.abort_session(state)
            else:
                await self.handling_unexpected_error(state)


class UpdateHabitName(Markup):
    def __init__(self, interface: Interface):
        super().__init__(interface)

    def _init_state(self):
        self._state = States.update_habit_name

    def _init_text_map(self):
        self.text_map = {
            "action": TextWidget(f"{Emoji.BULB} Enter the target name"),
        }

    def _init_markup_map(self):
        self.markup_map = [
            {
                "back": ButtonWidget(f"{Emoji.DENIAL} Cancel", "habits")
            }
        ]

    async def __call__(self, habit_id, name, session: ClientSession, state: FSMContext):
        if len(name) > MAX_NAME_LENGTH:
            await self.update_feedback(f"Maximum name length is {MAX_NAME_LENGTH} simbols")
            await self.open(state)
        elif not re.fullmatch(r'[\w\s]+', name, flags=re.I):
            await self.update_feedback(f"Name must contains only latin symbols or _ or spaces or digits")
            await self.open(state)
        else:
            async with session.patch(f'/update_habit_name/{habit_id}?name=name') as response:
                if response.status == 200:
                    await self._interface.habit_control_temp.text_map['name'].update_text(data=name)
                    await self._interface.habit_control_temp.open(state)
                elif response.status == 401:
                    await self.abort_session(state)
                else:
                    await self.handling_unexpected_error(state)


class UpdateHabitDescription(Markup):
    def __init__(self, interface: Interface):
        super().__init__(interface)

    def _init_state(self):
        self._state = States.update_habit_description

    def _init_text_map(self):
        self.text_map = {
            "action": TextWidget(f"{Emoji.BULB} Enter the description"),
        }

    async def __call__(self, habit_id, description, session: ClientSession, state: FSMContext):
        self.markup_map = [
            {
                "back": ButtonWidget(f"{Emoji.DENIAL} Cancel", ShowHabitCallbackData(id=habit_id))
            }
        ]
        if len(description) > MAX_DESCRIPTION_LENGTH:
            await self.update_feedback(f"Maximum description length is {MAX_DESCRIPTION_LENGTH} simbols")
            await self.open(state)
        elif not re.fullmatch(r'[\w\s]+', description, flags=re.I):
            await self.update_feedback(f"Description must contains only latin symbols or _ or spaces or digits")
            await self.open(state)
        else:
            async with session.patch(f'/update_habit_description/{description}?description=description') as response:
                if response.status == 200:
                    await self._interface.habit_control_temp.text_map['description'].update_text(data=description)
                    await self._interface.habit_control_temp.open(state)
                elif response.status == 401:
                    await self.abort_session(state)
                else:
                    await self.handling_unexpected_error(state)


class ConformDeleteHabit(Markup):
    def __init__(self, interface: Interface):
        super().__init__(interface)

    def _init_state(self):
        self._state = States.update_habit_description

    def _init_text_map(self):
        self.text_map = {
            "conform": DataTextWidget(f"{Emoji.RED_QUESTION} Do you really want to delete target", end='?'),
        }

    async def __call__(self, habit_id: int, state: FSMContext):
        self.markup_map = [
            {
                "conform": ButtonWidget(f"{Emoji.OK} Conform", ConformDeleteHabitCallbackData(id=habit_id)),
                "back": ButtonWidget(f"{Emoji.DENIAL} Cancel", ShowHabitCallbackData(id=habit_id))
            }
        ]
        await self.open(state)


class CreateHabitName(Markup):
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

    async def __call__(self, session: ClientSession, name, state):
        if len(name) > MAX_NAME_LENGTH:
            await self.update_feedback(f"Maximum name length is {MAX_NAME_LENGTH} simbols")
            await self.open(state)
        elif not re.fullmatch(r'[\w\s]+', name, flags=re.I):
            await self.update_feedback(f"Name must contains only latin symbols or _ or spaces or digits")
            await self.open(state)
        else:
            await self._interface.input_habit_border.open(state)


class CreateHabitBorder(Markup):
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
            self._interface.habit_manager.create_habit(session, border)

import re
from aiogram.fsm.context import FSMContext
from aiohttp import ClientSession

from frontend.FSM import States
from frontend.markups import MAX_NAME_LENGTH, MAX_DESCRIPTION_LENGTH
from frontend.markups.core import *


class ShowTargetCallbackData(CallbackData, prefix='show_target'):
    id: int


class UpdateTargetNameCallbackData(CallbackData, prefix='update_target_name'):
    id: int


class UpdateTargetDescriptionCallbackData(CallbackData, prefix='update_target_description'):
    id: int


class DeleteTargetCallbackData(CallbackData, prefix='delete_target'):
    id: int


class ConformDeleteTargetCallbackData(CallbackData, prefix='conform_delete_target'):
    id: int


class InvertCompletedTargetCallbackData(CallbackData, prefix='invert_completed_target'):
    id: int


class TargetsManager:
    def __init__(self, interface: Interface):
        self._interface = interface
        self.target_control_temp = TargetsControl(interface)
        self.show_up_targets = ShowUpTargets(interface)
        self.target = Target(interface)
        self.create_target_name = CreateTargetName(interface)
        self.create_target_border = CreateTargetBorder(interface)

    async def create_target(self, session, state):
        name = self.create_target_name.name
        border = self.create_target_border.target_border

        async with session.post('/create_target', json={
            "name": name,
            "border": border
        }) as response:
            if response.status == 200:
                await self._.update_feedback(f'target with name {name} created')
                await self.open(state)
            elif response.status == 401:
                await self._interface.close_session(state)
            else:
                await self._interface.markup.handling_unexpected_error(state)

    async def delete_target(self, target_id, session: ClientSession, state: FSMContext):
        async with session.delete(f'/delete_target/{target_id}') as response:
            if response.status == 200:
                await self.update_feedback(f'target with name {self._interface.targets_manager.show_up_targets_temp.targets[target_id]["name"]} created')
                await self._interface.show_up_targets_temp()
            elif response.status == 401:
                await self._interface.close_session(state)(state)
            else:
                await self.handling_unexpected_error(state)
                
                
class TargetsControl(Markup):
    def __init__(self, interface: Interface):
        super().__init__(interface)

    def _init_text_map(self):
        self.text_map = {
            "total_completed": DataTextWidget('Total completed targets'),
            "progress_today": DataTextWidget('Progress today')
        }

    def _init_markup_map(self):
        self.markup_map = [
            {
                "targets": ButtonWidget(f"{Emoji.DIAGRAM} Show up current targets", "current_targets"),
                "create_target": ButtonWidget(f'{Emoji.SPROUT} Create new target', 'create_target'),
                "show_completed": ButtonWidget(f"{Emoji.SHINE_STAR} Show completed targets", "show_completed_targets"),
            },
        ]

# id = Column(Integer, primary_key=True)
# name = Column(VARCHAR(MAX_NAME_LENGTH), nullable=False)
# description = Column(VARCHAR(MAX_DESCRIPTION_LENGTH), default='No description')
# completed = Column(Boolean, default=False)
# progress = Column(Integer, default=0)
# border_progress = Column(Integer, default=21)
#
# user_id = Column(Integer, ForeignKey('user.telegram_id'), nullable=False)


class ShowUpTargets(Markup):
    def __init__(self, interface: Interface):
        super().__init__(interface)
        self.targets = {}

    def _init_text_map(self):
        self.text_map = {
            "info": DataTextWidget(f'{Emoji.DIAGRAM} Marked targets today')
        }

    async def __call__(self, session: ClientSession, state: FSMContext):
        self.markup_map = []
        async with session.get('/show_up_targets') as response:
            if response.status == 200:
                targets_ = await response.json()
                total_completed = 0
                total_targets = len(targets_)

                for target in targets_:
                    if target.completed:
                        total_completed += 1
                        self.markup_map.append({
                            target.id: ButtonWidget(target.name, ShowtargetCallbackData(id=target.id), mark=Emoji.OK)
                        })
                    else:
                        self.markup_map.append({
                            target.id: ButtonWidget(target.name, ShowtargetCallbackData(id=target.id))
                        })

                    self.targets[target.id] = target

                await self.text_map['info'].update_text(data=f'{total_completed}/{total_targets}')
                await self.open(state)
            elif response.status == 401:
                await self._interface.close_session(state)
            else:
                await self.handling_unexpected_error(state)


class Target(Markup):
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
        target = self._interface.targets_manager.show_up_targets.targets[id_]

        await self.text_map['name'].update_text(data=target.name)

        if target.description is None:
            self.text_map['description'].off()
        else:
            await self.text_map['description'].update_text(data=target.description)

        await self.text_map['completed'].update_text(data=Emoji.OK if target.completed else Emoji.DENIAL)

        self.markup_map = [
            {
                "update_name": ButtonWidget('Update name', UpdatetargetNameCallbackData(id=target.id)),
                "update_description": ButtonWidget('Update description', UpdatetargetDescriptionCallbackData(id=target.id)),
                "delete_target": ButtonWidget('Delete', DeletetargetCallbackData(id=target.id)),
                "completed": ButtonWidget(f'{Emoji.DENIAL} Incomplete' if target.completed else f'{Emoji.OK} Complete', InvertCompletedtargetCallbackData(id=target.id))
            }
        ]
        await self.open(state)

    async def invert_complete(self, id_: int, session: ClientSession, state: FSMContext):
        async with session.patch(f'/invert_target_completed/{id_}') as response:
            if response.status == 200:
                response = await response.text()
                await self.markup_map[0]['completed'].update_button(text=f'{Emoji.DENIAL} Incomplete' if response == '1' else f'{Emoji.OK} Complete')
                await self.open(state)
            elif response.status == 401:
                await self._interface.close_session(state)(state)
            else:
                await self.handling_unexpected_error(state)


class UpdateTargetName(Markup):
    def __init__(self, interface: Interface):
        super().__init__(interface)

    def _init_state(self):
        self._state = States.update_target_name

    def _init_text_map(self):
        self.text_map = {
            "action": TextWidget(f"{Emoji.BULB} Enter the target name"),
        }

    def _init_markup_map(self):
        self.markup_map = [
            {
                "back": ButtonWidget(f"{Emoji.DENIAL} Cancel", "targets")
            }
        ]

    async def __call__(self, target_id, name, session: ClientSession, state: FSMContext):
        if len(name) > MAX_NAME_LENGTH:
            await self.update_feedback(f"Maximum name length is {MAX_NAME_LENGTH} simbols")
            await self.open(state)
        elif not re.fullmatch(r'[\w\s]+', name, flags=re.I):
            await self.update_feedback(f"Name must contains only latin symbols or _ or spaces or digits")
            await self.open(state)
        else:
            async with session.patch(f'/update_target_name/{target_id}?name=name') as response:
                if response.status == 200:
                    await self._interface.target_control_temp.text_map['name'].update_text(data=name)
                    await self._interface.target_control_temp.open(state)
                elif response.status == 401:
                    await self._interface.close_session(state)(state)
                else:
                    await self.handling_unexpected_error(state)


class UpdateTargetDescription(Markup):
    def __init__(self, interface: Interface):
        super().__init__(interface)

    def _init_state(self):
        self._state = States.update_target_description

    def _init_text_map(self):
        self.text_map = {
            "action": TextWidget(f"{Emoji.BULB} Enter the description"),
        }

    async def __call__(self, target_id, description, session: ClientSession, state: FSMContext):
        self.markup_map = [
            {
                "back": ButtonWidget(f"{Emoji.DENIAL} Cancel", ShowtargetCallbackData(id=target_id))
            }
        ]
        if len(description) > MAX_DESCRIPTION_LENGTH:
            await self.update_feedback(f"Maximum description length is {MAX_DESCRIPTION_LENGTH} simbols")
            await self.open(state)
        elif not re.fullmatch(r'[\w\s]+', description, flags=re.I):
            await self.update_feedback(f"Description must contains only latin symbols or _ or spaces or digits")
            await self.open(state)
        else:
            async with session.patch(f'/update_target_description/{description}?description=description') as response:
                if response.status == 200:
                    await self._interface.target_control_temp.text_map['description'].update_text(data=description)
                    await self._interface.target_control_temp.open(state)
                elif response.status == 401:
                    await self._interface.close_session(state)(state)
                else:
                    await self.handling_unexpected_error(state)


class ConformDeleteTarget(Markup):
    def __init__(self, interface: Interface):
        super().__init__(interface)

    def _init_state(self):
        self._state = States.update_target_description

    def _init_text_map(self):
        self.text_map = {
            "conform": DataTextWidget(f"{Emoji.RED_QUESTION} Do you really want to delete target", end='?'),
        }

    async def __call__(self, target_id: int, state: FSMContext):
        self.markup_map = [
            {
                "conform": ButtonWidget(f"{Emoji.OK} Conform", ConformDeletetargetCallbackData(id=target_id)),
                "back": ButtonWidget(f"{Emoji.DENIAL} Cancel", ShowtargetCallbackData(id=target_id))
            }
        ]
        await self.open(state)


class CreateTargetName(Markup):
    def __init__(self, interface: Interface):
        super().__init__(interface)
        self.name = None

    def _init_state(self):
        self._state = States.input_target_name

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
            await self._interface.targets_manager.input_target_border.open(state)


class CreateTargetBorder(Markup):
    def __init__(self, interface: Interface):
        super().__init__(interface)
        self.target_border = None

    def _init_state(self):
        self.state = States.input_target_border

    def _init_text_map(self):
        self.text_map = {
            "action": TextWidget('Enter target border at 1 to 999\n'
                                 '(By default border is 21 days. This value is standard for fixation target)')
        }

    def _init_markup_map(self):
        self.markup_map = [
            {
                "skip": ButtonWidget(f'{Emoji.SKIP} Skip', "create_target")
            }
        ]

    def __call__(self, border: str, state: FSMContext, session: ClientSession):
        if not re.fullmatch(r'\d{1,3}', border):
            self.update_feedback('Border value must be integer and at 1 to 999')
            self.open(state)
        else:
            self.target_border = int(border)
            self._interface.targets_manager.create_target(session, border)

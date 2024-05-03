import re
from aiogram.fsm.context import FSMContext
from aiohttp import ClientSession

from frontend.FSM import States
from frontend.markups import MAX_NAME_LENGTH, MAX_DESCRIPTION_LENGTH, MIN_BORDER_RANGE, MAX_BORDER_RANGE, \
    STANDARD_BORDER_RANGE
from frontend.markups.core import *

class CreateTargetCallbackData(CallbackData, prefix="create_target"):
    id: int

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
        self.targets_control = TargetsControl(interface)
        self.show_up_targets = ShowUpTargets(interface)
        self.target = Target(interface)
        self.create_target_name = CreateTargetName(interface)
        self.create_target_border = CreateTargetBorder(interface)
                
                
class TargetsControl(TextMarkup):
    def __init__(self, interface: Interface):
        super().__init__(
            interface,
            TextMap(
                {
                    "total_completed": DataTextWidget(header='Total completed targets'),
                    "progress_today": DataTextWidget(header='Progress today')
                }
            ),
            MarkupMap(
                [
                    {
                        "targets": ButtonWidget(
                            text=f"{Emoji.DIAGRAM} Show up current targets",
                            callback_data="current_targets"
                        ),
                        "create_target": ButtonWidget(
                            text=f'{Emoji.SPROUT} Create new target',
                            callback_data='create_target'
                        ),
                        "show_completed": ButtonWidget(
                            text=f"{Emoji.SHINE_STAR} Show completed targets",
                            callback_data="show_completed_targets"
                        ),
                    },
                ]
            )
        )

    async def create_target(self, session, state):
        name = self._interface.storage["target_name"]
        border = self._interface.storage["target_border"]

        async with session.post('/create_target', json={
            "name": name,
            "border": border
        }) as response:
            if response.status == 200:
                self._interface.feedback.data = f'{Emoji.SPROUT} Target with name {name} created'
                await self._interface.targets_manager.targets_control.open(state)
            elif response.status == 401:
                await self._interface.close_session(state)
            else:
                await self._interface.markup.handling_unexpected_error(state)

        self._interface.storage.update({"target_name": None, "target_border": STANDARD_BORDER_RANGE})

    async def delete_target(self, target_id, session: ClientSession, state: FSMContext):
        async with session.delete(f'/delete_target/{target_id}') as response:
            if response.status == 200:
                self._interface.feedback.data = f'{Emoji.DENIAL} Target with name {self._interface.storage["targets"][target_id]["name"]} deleted'
                await self._interface.targets_manager.show_up_targets.open(state)
            elif response.status == 401:
                await self._interface.close_session(state)
            else:
                await self._interface.handling_unexpected_error(state)


class ShowUpTargets(TextMarkup):
    def __init__(self, interface: Interface):
        super().__init__(
            interface,
            TextMap(
                {
                    "info": DataTextWidget(header=f'{Emoji.DIAGRAM} Marked targets today')
                }
            ),
        )

    async def __call__(self, session: ClientSession, state: FSMContext):
        self._interface.storage["targets"] = {}

        async with session.get('/show_up_targets') as response:
            if response.status == 200:
                targets_ = await response.json()
                total_completed = 0
                total_targets = len(targets_)

                for target in enumerate(targets_):
                    if target.completed:
                        total_completed += 1
                        self.markup_map.add_buttons(
                            {
                                target.id: ButtonWidget(
                                    text=target.name,
                                    callback_data=ShowTargetCallbackData(id=target.id),
                                    mark=Emoji.OK
                                )
                            }
                        )
                    else:
                        self.markup_map.add_buttons(
                            {
                                target.id: ButtonWidget(
                                    text=target.name,
                                    callback_data=ShowTargetCallbackData(id=target.id)
                                ),
                            }
                        )

                    self._interface.storage["targets"][target.id] = target

                self.text_map['info'].data = f'{total_completed}/{total_targets}'
                await self.open(state)
            elif response.status == 401:
                await self._interface.close_session(state)
            else:
                await self._interface.handling_unexpected_error(state)




class Target(TextMarkup):
    def __init__(self, interface: Interface):
        super().__init__(
            interface,
            TextMap(
                {
                    "name": DataTextWidget(header='Name'),
                    "description": DataTextWidget(header='Description'),
                    "percent_progress": DataTextWidget(header='Progress'),
                    "completed": DataTextWidget(header='Completed'),
                }
            ),
            MarkupMap(
                [
                    {
                        "update_name": ButtonWidget(text='Update name'),
                        "update_description": ButtonWidget(text='Update description'),
                        "delete_target": ButtonWidget(text='Delete'),
                        "completed": ButtonWidget()
                    }
                ]
            )
        )
    async def open(self, state, **kwargs):
        target = self._interface.storage["targets"][kwargs["target_id"]]

        self.text_map['name'].data = target.name

        if target.description is None:
            self.text_map['description'].off()
        else:
            self.text_map['description'].data = target.description

        percent_progress = round(target['progress'] / target['border'] * 100)
        quantity_green_squares = round(percent_progress / 100 * 10)
        view_progress = Emoji.GREEN_BIG_SQUARE * quantity_green_squares + Emoji.GREY_BUG_SQUARE * (10 - quantity_green_squares)
        self.text_map["percent_progress"].data = f"{view_progress}% {view_progress}"

        self.text_map['completed'].data = Emoji.OK if target.completed else Emoji.DENIAL

        self.markup_map["update_name"].callback_data = UpdateTargetNameCallbackData(id=target.id)
        self.markup_map["update_description"].callback_data = UpdateTargetDescriptionCallbackData(id=target.id)
        self.markup_map["delete_target"].callback_data = DeleteTargetCallbackData(id=target.id)
        self.markup_map["completed"].text = f'{Emoji.DENIAL} Incomplete' if target.completed else f'{Emoji.OK} Complete'
        self.markup_map["completed"].callback_data = InvertCompletedTargetCallbackData(id=target.id)
        await super().open(state)

    async def invert_complete(self, session: ClientSession, state: FSMContext, target_id: int):
        async with session.patch(f'/invert_target_completed/{target_id}') as response:
            if response.status == 200:
                response = await response.text()
                self.markup_map['completed'].text = f'{Emoji.DENIAL} Incomplete' if response == '1' else f'{Emoji.OK} Complete'
                await self.open(state, target_id=target_id)
            elif response.status == 401:
                await self._interface.close_session(state)
            else:
                await self._interface.handling_unexpected_error(state)


class UpdateTargetName(TextMarkup):
    def __init__(self, interface: Interface):
        super().__init__(
            interface,
            TextMap(
                {
                    "action": TextWidget(f"{Emoji.BULB} Enter the target name"),
                }
            ),
            MarkupMap(
                [
                    {
                        "back": ButtonWidget(text=f"{Emoji.DENIAL} Cancel")
                    }
                ]
            ),
            States.update_target_name

        )
    async def open(self, state, **kwargs):
        self.markup_map["back"].callback_data = ShowTargetCallbackData(id=kwargs["target_id"])
        await super().open(state)

    async def __call__(self, target_id: int, name: str, session: ClientSession, state: FSMContext):
        if len(name) > MAX_NAME_LENGTH:
            self._interface.feedback.data = f"Maximum name length is {MAX_NAME_LENGTH} simbols"
            await self.open(state, target_id=target_id)
        elif not re.fullmatch(r'[\w\s]+', name, flags=re.I):
            self._interface.feedback.data = f"Name must contains only latin symbols or _ or spaces or digits"
            await self.open(state, target_id=target_id)
        else:
            async with session.patch(f'/update_target_name/{target_id}?name={name}') as response:
                if response.status == 200:
                    self._interface.storage["targets"][target_id]["name"] = name
                    await self._interface.targets_manager.target.open(state, target_id=target_id)
                elif response.status == 401:
                    await self._interface.close_session(state)
                else:
                    await self._interface.handling_unexpected_error(state)


class UpdateTargetDescription(TextMarkup):
    def __init__(self, interface: Interface):
        super().__init__(
            interface,
            TextMap(
                {
                    "action": TextWidget(f"{Emoji.BULB} Enter the description"),
                }
            ),
            MarkupMap(
                [
                    {
                        "back": ButtonWidget(text=f"{Emoji.DENIAL} Cancel")
                    }
                ]
            ),
            States.update_target_description
        )

    async def open(self, state, **kwargs):
        self.markup_map["back"].callback_data = ShowTargetCallbackData(id=kwargs["target_id"])
        await super().open(state)

    async def __call__(self, target_id, description, session: ClientSession, state: FSMContext):
        if len(description) > MAX_DESCRIPTION_LENGTH:
            self._interface.feedback.data = f"Maximum description length is {MAX_DESCRIPTION_LENGTH} simbols"
            await self.open(state, target_id=target_id)
        elif not re.fullmatch(r'[\w\s]+', description, flags=re.I):
            self._interface.feedback.data = f"Description must contains only latin symbols or _ or spaces or digits"
            await self.open(state, target_id=target_id)
        else:
            async with session.patch(f'/update_target_description/{target_id}?description={description}') as response:
                if response.status == 200:
                    self._interface.storage["targets"][target_id]['description'] = description
                    await self._interface.targets_manager.target.open(state, target_id=target_id)
                elif response.status == 401:
                    await self._interface.close_session(state)
                else:
                    await self._interface.handling_unexpected_error(state)


class ConformDeleteTarget(TextMarkup):
    def __init__(self, interface: Interface):
        super().__init__(
            interface,
            TextMap(
                {
                    "conform": DataTextWidget(header=f"{Emoji.RED_QUESTION} Do you really want to delete target", end='?'),
                }
            ),
            MarkupMap(
                [
                    {
                        "conform": ButtonWidget(text=f"{Emoji.OK} Conform"),
                        "back": ButtonWidget(text=f"{Emoji.DENIAL} Cancel")
                    }
                ]
            ),
            States.update_target_description
        )
    async def open(self, state, **kwargs):
        self.markup_map["conform"].callback_data = ConformDeleteTargetCallbackData(id=kwargs["target_id"])
        self.markup_map["back"].callback_data = ShowTargetCallbackData(id=kwargs["target_id"])
        await super().open(state)


class CreateTargetName(TextMarkup):
    def __init__(self, interface: Interface):
        super().__init__(
            interface,
            TextMap(
                {
                    "action": TextWidget(f"{Emoji.BULB} Enter the target name"),
                }
            ),
            MarkupMap(
                [
                    {
                        "back": ButtonWidget(text=f"{Emoji.DENIAL} Cancel")
                    }
                ]
            ),
            States.create_target_name
        )
    async def open(self, state, **kwargs):
        self.markup_map["back"].callback_data = ShowTargetCallbackData(id=kwargs["target_id"])
        await super().open(state)
    async def __call__(self, session: ClientSession, name: str, state: FSMContext, target_id: int):
        self._interface.storage["border"] = STANDARD_BORDER_RANGE

        if len(name) > MAX_NAME_LENGTH:
            self._interface.feedback.data = f"Maximum name length is {MAX_NAME_LENGTH} simbols"
            await self.open(state, target_id=target_id)
        elif not re.fullmatch(r'[\w\s]+', name, flags=re.I):
            self._interface.feedback.data = f"Name must contains only latin symbols or _ or spaces or digits"
            await self.open(state, target_id=target_id)
        else:
            await self._interface.targets_manager.input_target_border.open(state, target_id=target_id)


class CreateTargetBorder(TextMarkup):
    def __init__(self, interface: Interface):
        super().__init__(
            interface,
            TextMap(
                {
                    "action": TextWidget(f'{Emoji.FLAG_FINISH} Enter target border at {MIN_BORDER_RANGE} to {MAX_BORDER_RANGE}\n'
                                         F'(By default border is {STANDARD_BORDER_RANGE} days. This value is standard for fixation target)')
                },
            ),
            MarkupMap(
                [
                    {
                        "skip": ButtonWidget(text=f'{Emoji.SKIP} Skip')
                    }
                ]
            ),
            States.create_target_border
        )
    async def open(self, state, **kwargs):
        self.markup_map["skip"].callback_data = CreateTargetCallbackData(id=kwargs["target_id"])
        await super().open(state)

    def __call__(self, session: ClientSession, state: FSMContext, border: str, target_id: int):
        if not re.fullmatch(r'\d{1,3}', border):
            self._interface.feedback.data = f'Border value must be integer and at {MIN_BORDER_RANGE} to {MAX_BORDER_RANGE}'
            self.open(state, target_id=target_id)
        else:
            self._interface.storage['target_border'] = int(border)
            self._interface.targets_manager.targets_control.create_target(session, state)

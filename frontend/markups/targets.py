import re

from aiogram.fsm.context import FSMContext
from aiohttp import ClientSession
from apscheduler.triggers.cron import CronTrigger

from frontend.bot.FSM import States
from frontend.markups.core import *
from frontend.utils import config, Emoji, storage
from frontend.utils.scheduler import scheduler, remainder

MAX_EMAIL_LENGTH = config.getint('limitations', 'MAX_EMAIL_LENGTH')
MAX_NAME_LENGTH = config.getint('limitations', 'MAX_NAME_LENGTH')
MAX_DESCRIPTION_LENGTH = config.getint('limitations', 'MAX_DESCRIPTION_LENGTH')
MAX_PASSWORD_LENGTH = config.getint('limitations', "MAX_PASSWORD_LENGTH")
MIN_BORDER_RANGE = config.getint('limitations', "MIN_BORDER_RANGE")
MAX_BORDER_RANGE = config.getint('limitations', "MAX_BORDER_RANGE")
STANDARD_BORDER_RANGE = config.getint('limitations', "STANDARD_BORDER_RANGE")


class ShowTargetCallbackData(CallbackData, prefix='show_target'):
    id: int


class TargetsManager:
    def __init__(self, interface):
        self._interface = interface

        self.targets_control = TargetsControl(interface)

        self.targets = Targets(interface)
        self.target = Target(interface)

        self.completed_targets = ShowCompletedTargets(interface)
        self.completed_target = CompletedTarget(interface)

        self.input_target_name = InputTargetName(interface)
        self.input_target_border = InputTargetBorder(interface)

        self.update_target_name = UpdateTargetName(interface)
        self.update_target_description = UpdateTargetDescription(interface)

        self.conform_delete_target = ConformDeleteTarget(interface)

        self.current_target_id = None

                
class TargetsControl(TextMarkup):
    def __init__(self, interface):
        super().__init__(
            interface,
            TextMap(
                {
                    "total_completed": DataTextWidget(header=f'{Emoji.SHINE_STAR} Total completed targets'),
                    "progress_today": DataTextWidget(header=f'{Emoji.DIAGRAM} Progress today')
                }
            ),
            MarkupMap(
                [
                    {
                        "targets": ButtonWidget(
                            text=f"{Emoji.DIAGRAM} Current targets",
                            callback_data="targets"
                        ),
                    },
                    {
                        "create_target_name": ButtonWidget(
                            text=f'{Emoji.SPROUT} Create new target',
                            callback_data='input_target_name'
                        ),
                    },
                    {
                        "completed_targets": ButtonWidget(
                            text=f"{Emoji.SHINE_STAR} Completed targets",
                            callback_data="completed_targets"
                        ),
                    },
                    {
                        "back": ButtonWidget(
                            text=f"{Emoji.BACK} Back",
                            callback_data="profile"
                        )
                    }
                ]
            )
        )

    async def open(self):
        async with self._interface.session.get('/completed_targets') as response:
            if response.status == 200:
                self.text_map["total_completed"].data = str(len(await response.json()))
            elif response.status == 401:
                await self._interface.close_session()
            else:
                await self._interface.handling_unexpected_error(response)

        async with self._interface.session.get('/targets') as response:
            if response.status == 200:
                total_targets = str(len(await response.json()))
                completed_targets_today = len([target for target in (await response.json()) if target["completed"]])
                self.text_map["progress_today"].data = f"{completed_targets_today}/{total_targets}"
            elif response.status == 401:
                await self._interface.close_session()
            else:
                await self._interface.handling_unexpected_error(response)

        await super().open()

    async def create_target(self):
        user_id = self._interface.chat_id
        name = storage.get(f"target_name:{user_id}")
        border = storage.get(f"target_border:{user_id}")

        async with self._interface.session.post('/create_target', json={
            "name": name,
            "border_progress": border
        }) as response:
            if response.status == 200:
                await self._interface.update_feedback(f'{Emoji.SPROUT} Target with name {name} created')
                async with self._interface.session.get(f'/notification_time/{await self._interface.encoded_chat_id()}') as response_:
                    time = await response_.json()
                    hour, minute = time["hour"], time['minute']
                await self._interface.targets_manager.targets_control.open()
                scheduler.add_job(func=remainder, trigger=CronTrigger(hour=hour, minute=minute), args=(self._interface.chat_id,), replace_existing=True, id=str(self._interface.chat_id))
            elif response.status == 401:
                await self._interface.close_session()
            else:
                await self._interface.handling_unexpected_error(response)

    async def delete_target(self):
        target_id = self._interface.targets_manager.current_target_id
        async with self._interface.session.delete(f'/delete_target/{target_id}') as response:
            if response.status == 200:
                async with self._interface.session.get(f"/is_all_done/{self._interface.encoded_chat_id}") as response_:
                    if await response_.text() == "1":
                        scheduler.remove_job(job_id=self._interface.chat_id)

                await self._interface.update_feedback(f'{Emoji.DENIAL} Target with name {self._interface.storage["targets"][target_id]["name"]} deleted')
                await self._interface.targets_manager.targets.open()

            elif response.status == 401:
                await self._interface.close_session()
            else:
                await self._interface.handling_unexpected_error(response)


class InputTargetName(TextMarkup):
    def __init__(self, interface):
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
            States.input_target_name
        )

    async def __call__(self, name: str):
        if len(name) > MAX_NAME_LENGTH:
            await self._interface.update_feedback(f"Maximum name length is {MAX_NAME_LENGTH} simbols", type_="error")
            await self.open()
        elif not re.fullmatch(r'[\w\s]+', name, flags=re.I):
            await self._interface.update_feedback(f"Name must contains only latin symbols or _ or spaces or digits", type_="error")
            await self.open()
        else:
            storage.set(f"target_name:{self._interface.chat_id}", name)
            await self._interface.targets_manager.input_target_border.open()


class InputTargetBorder(TextMarkup):
    def __init__(self, interface):
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
                        "skip": ButtonWidget(text=f'{Emoji.SKIP} Skip', callback_data="create_target")
                    }
                ]
            ),
            States.input_target_border
        )

    async def open(self):
        storage.set(f"target_border:{self._interface.chat_id}", STANDARD_BORDER_RANGE)
        await super().open()

    async def __call__(self, border: str):
        if not re.fullmatch(r'\d{1,3}', border):
            await self._interface.update_feedback(f'Border value must be integer and at {MIN_BORDER_RANGE} to {MAX_BORDER_RANGE}', type_="error")
            await self.open()
        else:
            storage.set(f"target_border:{self._interface.chat_id}", int(border))
            await self._interface.targets_manager.targets_control.create_target()


class Targets(TextMarkup):
    def __init__(self, interface):
        super().__init__(
            interface,
            TextMap(
                {
                    "info": DataTextWidget(header=f'{Emoji.DIAGRAM} Progress today')
                }
            ),
        )

    async def open(self):
        self._interface.targets_manager.current_target_id = None
        async with self._interface.session.get('/targets') as response:
            if response.status == 200:
                targets_ = await response.json()

                if not targets_:
                    await self._interface.update_feedback("No current targets so far", type_="info")
                    await self._interface.targets_manager.targets_control.open()
                    return

                total_completed = 0
                total_targets = len(targets_)

                for i, target in enumerate(targets_):
                    if target["completed"]:
                        total_completed += 1
                        await self.markup_map.add_buttons(
                            {
                                target.id: ButtonWidget(
                                    text=target["name"],
                                    callback_data=ShowTargetCallbackData(id=target["id"]),
                                    mark=Emoji.OK
                                )
                            }
                        )
                    else:
                        await self.markup_map.add_buttons(
                            {
                                target.id: ButtonWidget(
                                    text=target["name"],
                                    callback_data=ShowTargetCallbackData(id=target["id"]),
                                ),
                            }
                        )

                self.text_map['info'].data = f'{total_completed}/{total_targets}'
                await super().open()
            elif response.status == 401:
                await self._interface.close_session()
            else:
                await self._interface.handling_unexpected_error(response)


class Target(TextMarkup):
    def __init__(self, interface):
        super().__init__(
            interface,
            TextMap(
                {
                    "name": DataTextWidget(header=f'{Emoji.DART} Name'),
                    "description": DataTextWidget(header=f'{Emoji.LIST_WITH_PENCIL} Description'),
                    "percent_progress": DataTextWidget(header=f'{Emoji.TROPHY} Progress'),
                    "completed": DataTextWidget(header='Completed'),
                }
            ),
            MarkupMap(
                [
                    {
                        "update_name": ButtonWidget(text=f'{Emoji.NEW} Update name', callback_data="update_target_name"),
                        "update_description": ButtonWidget(text=f'{Emoji.NEW} Update description', callback_data="update_target_description"),
                        "delete_target": ButtonWidget(text=f'{Emoji.DENIAL} Delete', callback_data="conform_delete_target"),
                        "completed": ButtonWidget(callback_data="invert_completed")
                    },
                    {
                        "back": ButtonWidget(text=f"{Emoji.BACK}", callback_data="targets")
                    }
                ]
            )
        )

    async def open(self, **kwargs):
        self._interface.targets_manager.current_target_id = kwargs["target_id"]
        async with (self._interface.session.get(f"/target/{kwargs['target_id']}") as response):
            target = await response.json()

        self.text_map['name'].data = target["name"]

        if target.description is None:
            self.text_map['description'].off()
        else:
            self.text_map['description'].data = target["description"]

        percent_progress = round(target['progress'] / target['border'] * 100)
        quantity_green_squares = round(percent_progress / 100 * 10)
        view_progress = Emoji.GREEN_BIG_SQUARE * quantity_green_squares + Emoji.GREY_BUG_SQUARE * (10 - quantity_green_squares)
        self.text_map["percent_progress"].data = f"{percent_progress}% {view_progress}"

        self.text_map['completed'].data = Emoji.OK if target.completed else Emoji.DENIAL

        self.markup_map["completed"].text = f'{Emoji.DENIAL} Incomplete' if target.completed else f'{Emoji.OK} Complete'

        await super().open()

    async def invert_complete(self):
        target_id = self._interface.targets_manager.current_target_id
        async with self._interface.session.patch(f'/invert_target_completed/{target_id}') as response:
            if response.status == 200:
                response = await response.text()
                self.markup_map['completed'].text = f'{Emoji.DENIAL} Incomplete' if response == '1' else f'{Emoji.OK} Complete'
                self._interface.storage["targets"][target_id]["completed"] = True if response == '1' else False
                await self.open(target_id=target_id)

                async with self._interface.session.get("/is_all_done") as response_:
                    if await response_.text() == "1":
                        scheduler.remove_job(job_id=self._interface.chat_id)
                    elif response_.status == 401:
                        await self._interface.close_session()
            elif response.status == 401:
                await self._interface.close_session()
            else:
                await self._interface.handling_unexpected_error(response)


class UpdateTargetName(TextMarkup):
    def __init__(self, interface):
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

    async def __call__(self, name: str):
        target_id = self._interface.targets_manager.current_target_id
        if len(name) > MAX_NAME_LENGTH:
            await self._interface.update_feedback(f"Maximum name length is {MAX_NAME_LENGTH} simbols")
            await self.open()
        elif not re.fullmatch(r'[\w\s]+', name, flags=re.I):
            await self._interface.update_feedback(f"Name must contains only latin symbols or _ or spaces or digits")
            await self.open()
        else:
            async with self._interface.session.patch(f'/update_target_name/{target_id}?name={name}') as response:
                if response.status == 200:
                    await self._interface.targets_manager.target.open(target_id=target_id)
                elif response.status == 401:
                    await self._interface.close_session()
                else:
                    await self._interface.handling_unexpected_error(response)


class UpdateTargetDescription(TextMarkup):
    def __init__(self, interface):
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

    async def __call__(self, description: str):
        target_id = self._interface.targets_manager.current_target_id
        if len(description) > MAX_DESCRIPTION_LENGTH:
            await self._interface.update_feedback(f"Maximum description length is {MAX_DESCRIPTION_LENGTH} simbols")
            await self.open()
        elif not re.fullmatch(r'[\w\s]+', description, flags=re.I):
            await self._interface.update_feedback(f"Description must contains only latin symbols or _ or spaces or digits")
            await self.open()
        else:
            async with self._interface.session.patch(f'/update_target_description/{target_id}?description={description}') as response:
                if response.status == 200:
                    self._interface.targets_manager.target["description"].on()
                    self._interface.storage["targets"][target_id]['description'] = description
                    await self._interface.targets_manager.target.open(target_id=target_id)
                elif response.status == 401:
                    await self._interface.close_session()
                else:
                    await self._interface.handling_unexpected_error(response)


class ConformDeleteTarget(TextMarkup):
    def __init__(self, interface):
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
                        "conform": ButtonWidget(text=f"{Emoji.OK} Conform", callback_data="delete_target"),
                        "back": ButtonWidget(text=f"{Emoji.DENIAL} Cancel", callback_data="target")
                    }
                ]
            )
        )


class ShowCompletedTargetCallbackData(CallbackData, prefix="show_completed_target"):
    id: int


class ShowCompletedTargets(TextMarkup):
    def __init__(self, interface):
        super().__init__(
            interface,
            TextMap(
                {
                    "info": DataTextWidget(header="Total completed")
                }
            ),
        )

    async def open(self):
        async with self._interface.session.get('/completed_targets') as response:
            if response.status == 200:
                targets = await response.json()
                self.text_map["info"].data = len(targets)
                for target in targets:
                    await self.markup_map.add_buttons(
                        {
                            "name": ButtonWidget(
                                text=target["name"],
                                callback_data=ShowCompletedTargetCallbackData(id=self._interface.targets_manager.current_target_id)
                            )
                        }
                    )
                await super().open()
            elif response.status == 404:
                await self._interface.update_feedback("no completed targets so far")
                await self._interface.targets_manager.targets_control.open()
            elif response.status == 401:
                await self._interface.close_session()
            else:
                await self._interface.handling_unexpected_error(response)


class CompletedTarget(TextMarkup):
    def __init__(self, interface):
        super().__init__(
            interface,
            TextMap(
                {
                    "create_datetime": DataTextWidget(header="Create target date"),
                    "completed_datetime": DataTextWidget(header="Completed target date"),
                    "name": DataTextWidget(header=f'{Emoji.DART} Name'),
                    "description": DataTextWidget(header=f'{Emoji.LIST_WITH_PENCIL} Description'),
                }
            ),
            MarkupMap(
                [
                    {
                        "delete_target": ButtonWidget(text=f'{Emoji.DENIAL} Delete', callback_data="conform_delete_target"),
                    },
                    {
                        "back": ButtonWidget(text=f"{Emoji.BACK}", callback_data="completed_targets")
                    }
                ]
            )
        )

    async def open(self, **kwargs):
        self._interface.targets_manager.current_target_id = kwargs["target_id"]
        async with self._interface.session.get(f"/target/{kwargs['target_id']}") as response:
            target = await response.json()

        self.text_map['name'].data = target["name"]

        if target.description is None:
            self.text_map['description'].off()
        else:
            self.text_map['description'].data = target["description"]

        self.text_map["create_datetime"].data = target["create_datetime"]

        self.text_map['completed_datetime'].data = target["completed_datetime"]

        await super().open()

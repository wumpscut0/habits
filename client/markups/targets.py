# class Targets(TextMarkup):
#     def __init__(self, interface):
#         super().__init__(
#             interface,
#             TextMap(
#                 {
#                     "info": DataTextWidget(header=f'{Emoji.DIAGRAM} Progress today')
#                 }
#             ),
#         )
#
#     async def open(self):
#         storage.delete(f"target_id:{self._interface._user_id}")
#         response = self._interface.response_middleware()
#         if response is not None:
#             targets = await response.json()
#
#             if not targets:
#                 await self._interface.update_feedback("No current targets so far", type_="info")
#                 await self._interface.targets_manager.targets_control.open()
#                 return
#
#             targets = [target for target in targets if target["progress"] != target["border_progress"]]
#
#             total_completed = 0
#             total_targets = len(targets)
#             markup_map = MarkupMap()
#             for i, target in enumerate(targets):
#                 if target["completed"]:
#                     total_completed += 1
#                     await markup_map.add_buttons(
#                         {
#                             target["id"]: ButtonWidget(
#                                 text=target["name"],
#                                 callback_data=ShowTargetCallbackData(id=target["id"]),
#                                 mark=Emoji.OK
#                             )
#                         }
#                     )
#                 else:
#                     await markup_map.add_buttons(
#                         {
#                             target["id"]: ButtonWidget(
#                                 text=target["name"],
#                                 callback_data=ShowTargetCallbackData(id=target["id"]),
#                             ),
#                         }
#                     )
#
#             await markup_map.add_buttons(
#                 {
#                     "back": ButtonWidget(text=f"{Emoji.BACK} Back", callback_data="targets_control")
#                 }
#             )
#             self.markup_map = markup_map
#             self.text_map['info'].data = f'{total_completed}/{total_targets}'
#             await super().open()
#
#
# class Target(TextMarkup):
#     def __init__(self, interface):
#         super().__init__(
#             interface,
#             TextMap(
#                 {
#                     "name": DataTextWidget(header=f'{Emoji.DART} Name'),
#                     "description": DataTextWidget(header=f'{Emoji.LIST_WITH_PENCIL} Description'),
#                     "percent_progress": DataTextWidget(header=f'{Emoji.TROPHY} Progress'),
#                     "completed": DataTextWidget(header=f'{Emoji.INFO} Completed'),
#                 }
#             ),
#             MarkupMap(
#                 [
#                     {
#                         "update_name": ButtonWidget(text=f'{Emoji.UP} Update name', callback_data="update_target_name"),
#                         "update_description": ButtonWidget(text=f'{Emoji.UP} Update description', callback_data="update_target_description"),
#                     },
#                     {
#                         "delete_target": ButtonWidget(text=f'{Emoji.DENIAL} Delete', callback_data="conform_delete_target"),
#                         "completed": ButtonWidget(callback_data="invert_completed")
#                     },
#                     {
#                         "back": ButtonWidget(text=f"{Emoji.BACK} Back", callback_data="targets")
#                     }
#                 ]
#             )
#         )
#
#     async def open(self, **kwargs):
#         storage.set(f"target_id:{self._interface._user_id}", kwargs["target_id"])

#             response = await self._interface.response_middleware()
#             if response is not None:
#                 target = await response.json()
#                 self.text_map['name'].data = target["name"]
#
#                 if target["description"] is None:
#                     self.text_map['description'].off()
#                 else:
#                     self.text_map['description'].on()
#                     self.text_map['description'].data = target["description"]
#
#                 percent_progress = round(target['progress'] / target['border_progress'] * 100)
#                 quantity_green_squares = round(percent_progress / 100 * 10)
#                 view_progress = Emoji.GREEN_BIG_SQUARE * quantity_green_squares + Emoji.GREY_BUG_SQUARE * (10 - quantity_green_squares)
#                 self.text_map["percent_progress"].data = f"{percent_progress}% {view_progress}"
#
#                 self.text_map['completed'].data = Emoji.OK if target["completed"] else Emoji.DENIAL
#
#                 self.markup_map["completed"].text = f'{Emoji.DENIAL} Incomplete' if target["completed"] else f'{Emoji.OK} Complete'
#
#                 await super().open()
#
#     async def invert_complete(self):
#         target_id = storage.get(f"target_id:{self._interface._user_id}")

#             response = await self._interface.response_middleware(response)
#             if response is not None:
#                 self.markup_map['completed'].text = f'{Emoji.DENIAL} Incomplete' if response == '1' else f'{Emoji.OK} Complete'
#                 await self._interface.refresh_notifications(response)
#                 await self.open(target_id=target_id)
#
#
# class UpdateTargetName(TextMarkup):
#     def __init__(self, interface):
#         super().__init__(
#             interface,
#             TextMap(
#                 {
#                     "action": TextWidget(f"{Emoji.BULB} Enter the target name"),
#                 }
#             ),
#             MarkupMap(
#                 [
#                     {
#                         "back": ButtonWidget(text=f"{Emoji.DENIAL} Cancel", callback_data="targets_control")
#                     }
#                 ]
#             ),
#             States.update_target_name
#         )
#
#     async def __call__(self, name: str):
#
#
#
# class UpdateTargetDescription(TextMarkup):
#     def __init__(self, interface):
#         super().__init__(
#             interface,
#             TextMap(
#                 {
#                     "action": TextWidget(f"{Emoji.BULB} Enter the description"),
#                 }
#             ),
#             MarkupMap(
#                 [
#                     {
#                         "back": ButtonWidget(text=f"{Emoji.DENIAL} Cancel")
#                     }
#                 ]
#             ),
#             States.update_target_description
#         )
#
#     async def __call__(self, description: str):
#         target_id = storage.get(f"target_id:{self._interface._user_id}")
#
#
#
# class ConformDeleteTarget(TextMarkup):
#     def __init__(self, interface):
#         super().__init__(
#             interface,
#             TextMap(
#                 {
#                     "conform": DataTextWidget(header=f"{Emoji.RED_QUESTION} Do you really want to delete target", end='?'),
#                 }
#             ),
#             MarkupMap(
#                 [
#                     {
#                         "conform": ButtonWidget(text=f"{Emoji.OK} Conform", callback_data="delete_target"),
#                         "back": ButtonWidget(text=f"{Emoji.DENIAL} Cancel", callback_data="target")
#                     }
#                 ]
#             )
#         )
#
#
# class ShowCompletedTargetCallbackData(CallbackData, prefix="show_completed_target"):
#     id: int
#
#
# class CompletedTargets(TextMarkup):
#     def __init__(self, interface):
#         super().__init__(
#             interface,
#             TextMap(
#                 {
#                     "info": DataTextWidget(header="Total completed")
#                 }
#             ),
#         )
#
#     async def open(self):
#         response = self._interface.get_targets()
#         if response is not None:
#             targets = await response.json()
#             targets = [target for target in targets if target["progress"] == target["border_progress"]]
#             if not targets:
#                 await self._interface.update_feedback("no completed targets so far", type_="info")
#                 await self._interface.targets_manager.targets_control.open()
#                 return
#
#             self.text_map["info"].data = str(len(targets))
#             markup_map = MarkupMap()
#             for target in targets:
#                 await markup_map.add_buttons(
#                     {
#                         "name": ButtonWidget(
#                             text=target["name"],
#                             callback_data=ShowCompletedTargetCallbackData(id=self._interface.targets_manager.current_target_id)
#                         )
#                     }
#                 )
#             await markup_map.add_buttons(
#                 {
#                     "back": ButtonWidget(text=f"{Emoji.BACK} Back", callback_data="targets_control")
#                 }
#             )
#             self.markup_map = markup_map
#             await super().open()
#
#
# class CompletedTarget(TextMarkup):
#     def __init__(self, interface):
#         super().__init__(
#             interface,
#             TextMap(
#                 {
#                     "create_datetime": DataTextWidget(header="Create target date"),
#                     "completed_datetime": DataTextWidget(header="Completed target date"),
#                     "name": DataTextWidget(header=f'{Emoji.DART} Name'),
#                     "description": DataTextWidget(header=f'{Emoji.LIST_WITH_PENCIL} Description'),
#                 }
#             ),
#             MarkupMap(
#                 [
#                     {
#                         "delete_target": ButtonWidget(text=f'{Emoji.DENIAL} Delete', callback_data="conform_delete_target"),
#                     },
#                     {
#                         "back": ButtonWidget(text=f"{Emoji.BACK}", callback_data="completed_targets")
#                     }
#                 ]
#             )
#         )
#
#     async def open(self, **kwargs):
#         storage.set(f"target_id:{self._interface._user_id}", kwargs["target_id"])
#
#             response = await self._interface.response_middleware(response)
#             if response is not None:
#                 target = await response.json()
#
#                 self.text_map['name'].data = target["name"]
#
#                 if target.description is None:
#                     self.text_map['description'].off()
#                 else:
#                     self.text_map['description'].data = target["description"]
#
#                 self.text_map["create_datetime"].data = target["create_datetime"]
#
#                 self.text_map['completed_datetime'].data = target["completed_datetime"]
#
#                 await super().open()

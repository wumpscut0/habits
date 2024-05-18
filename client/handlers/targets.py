from aiogram.types import CallbackQuery
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message

from client.markups.targets import ShowTargetCallbackData
from client.bot.FSM import States


targets_router = Router()


# @targets_router.callback_query(F.data == 'targets_control')
# async def open_targets_control(callback: CallbackQuery, interface: Interface):
#     await interface.targets_manager.targets_control.open()
#
#
# ########################################################################################################################
#
#
# @targets_router.callback_query(F.data == "input_target_name")
# async def open_input_target_name(callback: CallbackQuery, interface: Interface):
#     await interface.targets_manager.input_target_name.open()
#
#
# @targets_router.message(StateFilter(States.input_target_name), F.text)
# async def input_target_name(message: Message, interface: Interface):
#     await interface.targets_manager.input_target_name(message.text)
#     await message.delete()
#
#
# @targets_router.message(StateFilter(States.input_target_border), F.text)
# async def input_target_border(message: Message, interface: Interface):
#     await interface.targets_manager.input_target_border(message.text)
#     await message.delete()
#
#
# @targets_router.callback_query(F.data == "create_target")
# async def create_target(callback: CallbackQuery, interface: Interface):
#     await interface.targets_manager.targets_control.create_target()
#
#
# ########################################################################################################################
#
#
# @targets_router.callback_query(F.data == "completed_targets")
# async def open_completed_targets(callback: CallbackQuery, interface: Interface):
#     await interface.targets_manager.completed_targets.open()
#
#
# @targets_router.callback_query(ShowCompletedTargetCallbackData.filter())
# async def completed_target(callback: CallbackQuery, callback_data: ShowCompletedTargetCallbackData, interface: Interface):
#     await interface.targets_manager.completed_target.open(target_id=callback_data.id)
#
#
# ########################################################################################################################
#
#
# @targets_router.callback_query(F.data == "targets")
# async def open_targets(callback: CallbackQuery, interface: Interface):
#     await interface.targets_manager.targets.open()
#
#
# @targets_router.callback_query(ShowTargetCallbackData.filter())
# async def open_target(callback: CallbackQuery, callback_data: ShowTargetCallbackData, interface: Interface):
#     await interface.targets_manager.target.open(target_id=callback_data.id)
#
#
# @targets_router.callback_query(F.data == "target")
# async def open_target(callback: CallbackQuery, callback_data: ShowTargetCallbackData, interface: Interface):
#     await interface.targets_manager.target.open()
#
#
# @targets_router.callback_query(F.data == "invert_completed")
# async def invert_completed(callback: CallbackQuery, interface: Interface):
#     await interface.targets_manager.target.invert_complete()
#
#
# ########################################################################################################################
#
#
# @targets_router.callback_query(F.data == "update_target_name")
# async def open_update_target_name(callback: CallbackQuery, interface: Interface):
#     await interface.targets_manager.update_target_name.open()
#
#
# @targets_router.message(StateFilter(States.update_target_name), F.text)
# async def update_target_name(message: Message, interface: Interface):
#     await interface.targets_manager.update_target_name(message.text)
#     await message.delete()
#
#
# ########################################################################################################################
#
#
# @targets_router.callback_query(F.data == "update_target_description")
# async def open_update_target_description(callback: CallbackQuery, interface: Interface):
#     await interface.targets_manager.update_target_description.open()
#
#
# @targets_router.message(StateFilter(States.update_target_description), F.text)
# async def update_target_description(message: Message, interface: Interface):
#     await interface.targets_manager.update_target_description(message.text)
#     await message.delete()
#
#
# ########################################################################################################################
#
#
# @targets_router.callback_query(F.data == "conform_delete_target")
# async def open_conform_delete_target(callback: CallbackQuery, interface: Interface):
#     await interface.targets_manager.conform_delete_target.open()
#
#
# @targets_router.callback_query(F.data == "delete_target")
# async def delete_target(callback: CallbackQuery, interface: Interface):
#     await interface.targets_manager.targets_control.delete_target()

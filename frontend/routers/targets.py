from aiohttp import ClientSession
from aiogram.types import CallbackQuery
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from frontend.markups.targets import ShowTargetCallbackData, ShowCompletedTargetCallbackData
from frontend.controller import Interface
from frontend.bot.FSM import States


targets_router = Router()


@targets_router.callback_query(F.data == 'targets_control')
async def open_targets_control(callback: CallbackQuery, interface: Interface):
    await interface.targets_manager.targets_control.state()


########################################################################################################################


@targets_router.callback_query(F.data == "create_target_name")
async def open_create_target_name(callback: CallbackQuery, interface: Interface, state: FSMContext):
    await interface.targets_manager.create_target_name.open(state)


@targets_router.message(StateFilter(States.create_target_name), F.text)
async def create_target_name(message: Message, interface: Interface, state: FSMContext, session: ClientSession):
    await interface.targets_manager.create_target_name(message.text, session, state)


@targets_router.message(StateFilter(States.create_target_border), F.text)
async def create_target_border(message: Message, interface: Interface, state: FSMContext, session: ClientSession):
    await interface.targets_manager.create_target_border(message.text, session, state)


@targets_router.callback_query(F.data == "create_target")
async def create_target(callback: CallbackQuery, interface: Interface, state: FSMContext, session: ClientSession):
    await interface.targets_manager.targets_control.create_target(session, state)


########################################################################################################################


@targets_router.callback_query(F.data == "completed_targets")
async def open_completed_targets(callback: CallbackQuery, interface: Interface, state: FSMContext, session: ClientSession):
    await interface.targets_manager.show_up_complete_targets.open(state, session=session)


@targets_router.callback_query(ShowCompletedTargetCallbackData.filter())
async def completed_target(callback: CallbackQuery, callback_data: ShowCompletedTargetCallbackData, interface: Interface, state: FSMContext, session: ClientSession):
    await interface.targets_manager.completed_target.open(state, session=session, target_id=callback_data.id)


########################################################################################################################


@targets_router.callback_query(F.data == "targets")
async def open_targets(callback: CallbackQuery, interface: Interface, state: FSMContext, session: ClientSession):
    await interface.targets_manager.show_up_targets.open(state, session=session)


@targets_router.callback_query(ShowTargetCallbackData.filter())
async def open_target(callback: CallbackQuery, callback_data: ShowTargetCallbackData, interface: Interface, state: FSMContext, session: ClientSession):
    await interface.targets_manager.target.open(state, session=session, target_id=callback_data.id)


@targets_router.callback_query(F.data == "invert_completed")
async def invert_completed(callback: CallbackQuery, interface: Interface, state: FSMContext, session: ClientSession):
    await interface.targets_manager.target.invert_complete(session, state)


########################################################################################################################


@targets_router.callback_query(F.data == "update_target_name")
async def open_update_target_name(callback: CallbackQuery, interface: Interface, state: FSMContext):
    await interface.targets_manager.update_target_name.open(state)


@targets_router.message(StateFilter(States.update_target_name), F.text)
async def input_target_name(message: Message, interface: Interface, state: FSMContext, session: ClientSession):
    await interface.targets_manager.update_target_name.open(message.text, session, state)


########################################################################################################################


@targets_router.callback_query(F.data == "update_target_description")
async def open_update_target_description(callback: CallbackQuery, interface: Interface, state: FSMContext):
    await interface.targets_manager.update_target_description.open(state)


@targets_router.message(StateFilter(States.update_target_description), F.text)
async def input_target_description(message: Message, interface: Interface, state: FSMContext, session: ClientSession):
    await interface.targets_manager.update_target_description(message.text, session, state)


########################################################################################################################


@targets_router.callback_query(F.data == "conform_delete_target")
async def open_conform_delete_target(callback: CallbackQuery, interface: Interface, state: FSMContext):
    await interface.targets_manager.conform_delete_target.open(state)


@targets_router.callback_query(F.data == "delete_target")
async def delete_target(callback: CallbackQuery, interface: Interface, state: FSMContext):
    await interface.targets_manager.targets_control.delete_target()


########################################################################################################################


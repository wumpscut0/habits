from frontend.markups.targets import ShowTargetCallbackData
from frontend.routers import *


target_router = Router()


@target_router.callback_query(F.data == 'targets_control')
async def open_targets_control(callback: CallbackQuery, interface: Interface, state: FSMContext):
    await interface.targets_manager.targets_control.state(state)


########################################################################################################################


@target_router.callback_query(F.data == "targets")
async def open_targets(callback: CallbackQuery, interface: Interface, state: FSMContext, session: ClientSession):
    await interface.targets_manager.show_up_targets.open(state, session=session)


########################################################################################################################

@target_router.callback_query(ShowTargetCallbackData.filter())
async def open_target(callback: CallbackQuery, callback_data: ShowTargetCallbackData, interface: Interface, state: FSMContext, session: ClientSession):
    await interface.targets_manager.target.open(state, session=session, target_id=callback_data.id)


########################################################################################################################


@target_router.callback_query(F.data == "update_target_name")
async def open_update_target_name(callback: CallbackQuery, interface: Interface, state: FSMContext, session: ClientSession):
    await interface.targets_manager.update_target_name.open(state)


@target_router.message(StateFilter(States.update_target_name), F.text)
async def input_target_name(message: Message, interface: Interface, state: FSMContext, session: ClientSession):
    await interface.targets_manager.update_target_name()


########################################################################################################################

@target_router.callback_query(ShowTargetCallbackData.filter())
async def open_target(callback: CallbackQuery, callback_data: ShowTargetCallbackData, interface: Interface, state: FSMContext, session: ClientSession):
    await interface.targets_manager.target.open(state, target_id=callback_data.id)


@target_router.callback_query(ShowTargetCallbackData.filter())
async def open_target(callback: CallbackQuery, callback_data: ShowTargetCallbackData, interface: Interface, state: FSMContext, session: ClientSession):
    await interface.targets_manager.target.open(state, target_id=callback_data.id)


@target_router.callback_query(ShowTargetCallbackData.filter())
async def open_target(callback: CallbackQuery, callback_data: ShowTargetCallbackData, interface: Interface, state: FSMContext, session: ClientSession):
    await interface.targets_manager.target.open(state, target_id=callback_data.id)


@target_router.callback_query(ShowTargetCallbackData.filter())
async def open_target(callback: CallbackQuery, callback_data: ShowTargetCallbackData, interface: Interface, state: FSMContext, session: ClientSession):
    await interface.targets_manager.target.open(state, target_id=callback_data.id)



########################################################################################################################


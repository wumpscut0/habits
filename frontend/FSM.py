from aiogram.fsm.state import StatesGroup, State


# class StateManager:
#     def __init__(self, state: State | None = None):
#         self._state = state
#         self._default_state = self._state
#
#     @property
#     def state(self):
#         return self._state
#
#     @state.setter
#     def state(self, state):
#         self._state = state
#
#     async def reset(self):
#         self._state = self._default_state


class States(StatesGroup):
    input_password = State()
    repeat_password = State()
    input_email = State()
    input_verify_email_code = State()
    sign_in_with_password = State()
    input_habit_name = State()
    input_habit_border = State()


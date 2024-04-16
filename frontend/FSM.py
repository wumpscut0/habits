from aiogram.fsm.state import State, StatesGroup


class User(StatesGroup):
    input_nickname = State()
    input_login = State()
    input_password = State()
    repeat_password = State()

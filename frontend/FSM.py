from aiogram.fsm.state import State, StatesGroup





class SignInState(StatesGroup):
    input_login = State()
    input_password = State()


class SignUpState(StatesGroup):
    input_nickname = State()
    input_login = State()
    input_password = State()
    repeat_password = State()

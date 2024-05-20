from aiogram.fsm.state import StatesGroup, State


class States(StatesGroup):
    abyss_input = State()

    input_password = State()
    repeat_password = State()
    input_email = State()
    input_verify_email_code = State()
    sign_in_with_password = State()
    input_target_name = State()
    input_target_border = State()
    update_target_name = State()
    update_target_description = State()
    input_verify_code_reset_password = State()

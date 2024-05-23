from aiogram.fsm.state import StatesGroup, State


class States(StatesGroup):
    input_text_to_admin = State()
    input_text_password = State()
    input_text_repeat_password = State()
    input_text_email = State()
    input_text_verify_email_code = State()
    input_text_sign_in_with_password = State()
    input_text_target_name = State()
    input_text_target_description = State()
    input_text_target_border = State()
    input_text_update_target_name = State()
    input_text_update_target_description = State()
    input_text_verify_code_reset_password = State()

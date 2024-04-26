from frontend.routers import *


password_router = Router()


@password_router.message(StateFilter(States.sign_in_with_password), F.text)
async def sign_in_with_password(message: Message, interface: Interface, state: FSMContext, session: ClientSession):
    await interface.sign_in_with_password.sign_in_with_password(state, session, message.text)
    await message.delete()


@password_router.message(StateFilter(States.input_password), F.text)
async def input_new_password(message: Message, interface: Interface, state: FSMContext):
    await interface.input_password.input_password(state, message.text)
    await message.delete()


@password_router.message(StateFilter(States.repeat_password), F.text)
async def repeat_new_password(message: Message, interface: Interface, state: FSMContext):
    await interface.repeat_password.repeat_password(message.text, state)
    await message.delete()


@password_router.message(StateFilter(States.input_email), F.text)
async def input_email(message: Message, interface: Interface, state: FSMContext):
    await interface.input_email.input_email(message.text, state)
    await message.delete()


@password_router.message(StateFilter(States.input_verify_email_code), F.text)
async def input_verify_email_code(message: Message, interface: Interface, state: FSMContext):
    await interface.input_verify_email_code.verify_email(message.text, state)
    await message.delete()

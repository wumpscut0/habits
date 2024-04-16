from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest
from frontend import bot
from frontend.interface.sign_in import sign_in_router
from frontend.markups.authorization import Authorization
from frontend.markups.sign_in import SignIn

authorization_router = Router()
authorization_router.include_routers(
    sign_in_router
)


@authorization_router.message(CommandStart())
async def open_authorization(message: Message, state: FSMContext):
    current_data = await state.get_data()

    try:
        await bot.edit_message_text(chat_id=message.chat.id, message_id=current_data.get('message_id'), text='Session close')
    except TelegramBadRequest:
        pass

    authorization = Authorization()
    current_data = {
        "authorization": await authorization.serialize(),
        "sign_in": await SignIn().serialize()
    }
    message = await message.answer(text=await authorization.text, reply_markup=await authorization.markup)
    current_data["message_id"] = message.message_id
    await state.update_data(current_data)

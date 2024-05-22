from aiogram.types import CallbackQuery
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message

from client.markups.targets import ShowTargetCallbackData
from client.bot.FSM import States


targets_router = Router()
if len(name) > MAX_NAME_LENGTH:
#             await self._interface.update_feedback(f"Maximum name length is {MAX_NAME_LENGTH} simbols", type_="error")
#             await self.open()
#         elif not re.fullmatch(r'[\w\s]+', name, flags=re.I):
#             await self._interface.update_feedback(f"Name must contains only latin symbols or _ or spaces or digits", type_="error")
#             await self.open()
#         else:
#             storage.set(f"target_name:{self._interface._user_id}", name)
#             await self._interface.targets_manager.input_target_border.open()


try:
# border = int(border)
#         except ValueError:
#             await self._interface.update_feedback(f"Border value must be integer")
#         if not MIN_BORDER_RANGE <= border <= MAX_BORDER_RANGE:
#             await self._interface.update_feedback(f'Border range must be at {MIN_BORDER_RANGE} to {MAX_BORDER_RANGE}', type_="error")
#             await self.open()
#         else:
#             storage.set(f"target_border:{self._interface._user_id}", int(border))
#             await self._interface.targets_manager.targets_control.create_target()

target_id = storage.get(f"target_id:{self._interface._user_id}")
#         if len(name) > MAX_NAME_LENGTH:
#             await self._interface.update_feedback(f"Maximum name length is {MAX_NAME_LENGTH} simbols")
#             await self.open()
#         elif not re.fullmatch(r'[\w\s]+', name, flags=re.I):
#             await self._interface.update_feedback(f"Name must contains only latin symbols or _ or spaces or digits")
#             await self.open()
#         else:
#

 if len(description) > MAX_DESCRIPTION_LENGTH:
#             await self._interface.update_feedback(f"Maximum description length is {MAX_DESCRIPTION_LENGTH} simbols")
#             await self.open()
#         elif not re.fullmatch(r'[\w\s,?!:.]+', description, flags=re.I):
#             await self._interface.update_feedback(
#                 f"Description must contains only latin symbols or _ or , or ? or ! or : or . or spaces or digits",
#                 type_="error"
#             )
#             await self.open()
#         else:
#
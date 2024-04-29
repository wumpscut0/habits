from typing import List
from aiogram.fsm.context import FSMContext
from aiohttp import ClientSession

from config import Emoji
from frontend.markups import Markup, ButtonWidget, CommonButtons, DataTextWidget, TextWidget
from frontend.markups.habits import Habits
from frontend.markups.interface import Interface
from frontend.markups.auth import InputNewPassword, SignInWithPassword


class Profile(Markup):
    def __init__(self, interface: Interface):
        super().__init__(interface)

    def _inittext_map(self):
        self.text_map = {
            "hello": DataTextWidget('Hello', sep=', '),
        }

    def _init_markup_map(self):
        self.markup_map = [
            {
                "habits": ButtonWidget(f"{Emoji.DIAGRAM} Show up current targets", "habits"),
                "create_habit": ButtonWidget(f'f{Emoji.SPROUT} Create new target', 'create_habit')
            },
            {
                "options": ButtonWidget(f'{Emoji.GEAR️} Options', "options")
            },
            {
                "title_screen": ButtonWidget(f'{Emoji.BACK} Exit', "title_screen")
            }
        ]

    async def open(self, state):
        await self.text_map['hello'].update_text(data=self._interface.first_name)
        await super().open(state)
        
        
class Options(Markup):
    def __init__(self, interface: Interface):
        super().__init__(interface)
        
    def _init_text_map(self):
        self.text_map = {
            "action": TextWidget(f'{Emoji.GEAR️} Choose option')
        }
        
    def _init_markup_map(self):
        self.markup_map = [
            {
                "update_password": ButtonWidget(f"{Emoji.KEY}{Emoji.PLUS} Add password", "update_password"),
                "delete_password": ButtonWidget(f"{Emoji.KEY}{Emoji.DENIAL} Remove password", "delete_password",
                                                active=False)
            },
            # {
            #     "update_email": ButtonWidget(f"{Emoji.ENVELOPE} Add email", "update_email"),
            #     "delete_email": ButtonWidget(f"{Emoji.ENVELOPE} Remove email", "delete_email",
            #                                  active=False),
            # }
        ]

    async def update_password(self, session: ClientSession, state: FSMContext):
        await self._interface.password_resume.markup_map[0]['accept_password'].update_button(callback_data='update_password')
        await self.markup_map[0]['update_password'].update_button(text=f'{Emoji.KEY}{Emoji.UP} Update password')
        await self.markup_map[0]['delete_password'].update_button(active=True)
        async with session.patch('/update_password', json={
            "hash": self._interface.repeat_password.hash,
            "email": self._interface.input_email.email
        }) as response:
            if response.status == 200:
                await self.update_feedback(f'{Emoji.OK} Password and email updated')
                await self._interface.profile.open(state)
            elif response.status == 401:
                await self.abort_session(state)
            else:
                await self.handling_unexpected_error(state)
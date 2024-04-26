from frontend.markups import *


class TitleScreen(Markup):
    def __init__(self, interface: Interface):
        super().__init__()
        self._interface = interface

    def _init_text_map(self):
        self._text_map = {
            "info": TextWidget(f"{Emoji.BRAIN} Psychological service"),
            "feedback": CommonTexts.feedback()
        }

    def _init_markup_map(self):
        self._markup_map = [
            {
                "sign_in": ButtonWidget(f'{Emoji.DOOR}', 'try_profile'),
                "notifications": ButtonWidget("Notifications", "invert notifications", mark=Emoji.BELL)
            }
        ]

    async def invert_notifications(self, session: ClientSession, state: FSMContext):
        async with session.patch('/invert_notifications', json={'telegram_id': self._interface.chat_id}) as response:
            response = await response.text()
            if response == '1':
                mark = Emoji.BELL
                await self._markup_map[0]['notifications'].update_button(mark=mark)
                await self._text_map['feedback'].reset()
            elif response == '0':
                mark = Emoji.NOT_BELL
                await self._markup_map[0]['notifications'].update_button(mark=mark)
                await self._text_map['feedback'].reset()

            else:
                await self._text_map['feedback'].update_text('Internal server error')

        await self._interface.update(state, self)

    async def authorization(self, session: ClientSession, state: FSMContext):
        async with session.post('/sign_in', json={'telegram_id': self._interface.chat_id}) as response:
            if response.status == 400:
                await self._text_map['feedback'].reset()
                await self._interface.update(state, self._interface.sign_in_with_password)
            elif response.status == 200:
                await self._text_map['feedback'].reset()
                await self._interface.update(state, self._interface.profile)
            else:
                await self._text_map['feedback'].update_text('Internal server error')
                await self._interface.update(state, self)

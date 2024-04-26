from typing import List
from aiogram.fsm.context import FSMContext
from aiohttp import ClientSession
from config import Emoji
from frontend.markups.habits import Habits
from frontend.markups.interface import Interface
from frontend.markups.auth import InputNewPassword, SignInWithPassword
from frontend.markups.core import Markup, TextWidget, DataTextWidget, ButtonWidget, CommonTexts, CommonButtons

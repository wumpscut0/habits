import os

from aiogram import Bot

bot = Bot(os.getenv('TOKEN'), parse_mode='HTML')

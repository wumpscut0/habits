from os import getenv
from aiogram import Bot
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

bot = Bot(getenv('TOKEN'), parse_mode='HTML')

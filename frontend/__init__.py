import logging
from logging.config import dictConfig
from os import getenv
from aiogram import Bot
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": '%(asctime)s | %(message)s'
            }
        },
        "handlers": {
            "errors": {
                "class": "logging.FileHandler",
                "formatter": "default",
                "filename": "errors.log",
            },
            "info": {
                "class": "logging.FileHandler",
                "formatter": "default",
                "filename": "info.log",
            }
        },
        "loggers": {
            "errors": {
                "level": logging.ERROR,
                "handlers": [
                    "errors"
                ]
            }
        }
    }
dictConfig(config)
errors = logging.getLogger("errors")
info = logging.getLogger('info')

bot = Bot(getenv('TOKEN'), parse_mode='HTML')

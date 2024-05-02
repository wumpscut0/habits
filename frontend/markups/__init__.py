import os
import secrets
from string import digits
from email.mime.text import MIMEText

import aiosmtplib

from frontend import config

MAX_EMAIL_LENGTH = config.get('limitations', 'MAX_EMAIL_LENGTH')
MAX_NAME_LENGTH = config.get('limitations', 'MAX_NAME_LENGTH')
MAX_DESCRIPTION_LENGTH = config.get('limitations', 'MAX_DESCRIPTION_LENGTH')
MAX_PASSWORD_LENGTH = config.get('limitations', "MAX_PASSWORD_LENGTH")
MIN_BORDER_RANGE = config.get('limitations', "MIN_BORDER_RANGE")
MAX_BORDER_RANGE = config.get('limitations', "MAX_BORDER_RANGE")

MAIL_ADDRESS = os.getenv('ORGANIZATION_EMAIL')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
PORT = config.get('mailing', 'PORT')
SMTP_SERVER = config.get('mailing', 'SMTP_SERVER')


class Mailing:
    @classmethod
    async def _generate_secret_key(cls):
        return ''.join((secrets.choice(digits) for _ in range(6)))

    @classmethod
    async def verify_email(cls, receiver):
        verify_code = cls._generate_secret_key()
        message = MIMEText(f'Your verify code: {verify_code}')
        message['To'] = receiver
        message['From'] = MAIL_ADDRESS
        message['Subject'] = 'Verify email'
        async with aiosmtplib.SMTP(hostname=SMTP_SERVER, username=MAIL_ADDRESS, port=PORT, password=SMTP_PASSWORD,
                                   start_tls=True) as session:
            await session.sendmail(MAIL_ADDRESS, receiver, message.as_string())
        return verify_code


class Emoji:
    OK = "✅"
    DENIAL = "❌"
    BACK = "⬇️"
    KEY = "🔑"
    DOOR = "🚪"
    BRAIN = "🧠"
    MEGAPHONE = "📢"
    SHINE_STAR = "🌟"
    WARNING = "⚠️"
    SHIELD = "🛡"
    CYCLE = "🔄"
    BELL = "🔔"
    NOT_BELL = "🔕"
    TARGET = "🎯"
    EYE = "👁"
    SPROUT = "🌱"
    DIAGRAM = "📊"
    BULB = "💡"
    GEAR = "⚙️"
    ENVELOPE = "✉️"
    LOCK_AND_KEY = "🔐"
    PLUS = "➕"
    UP = "🆙"
    SKIP = "⏭️"
    GREEN_BIG_SQUARE = "🟩"
    RED_QUESTION = "❓"
    GREY_QUESTION = "❔"
    BAN = "🚫"
    GREEN_CIRCLE = "🟢"
    YELLOW_CIRCLE = "🟡"
    ORANGE_CIRCLE = "🟠"
    RED_CIRCLE = "🔴"

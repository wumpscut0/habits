import aiosmtplib
import secrets
import string
import os
from email.mime.text import MIMEText

from fastapi import FastAPI

from backend import config

app = FastAPI()

MAIL_ADDRESS = os.getenv('ORGANIZATION_EMAIL')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
PORT = config.get('mailing', 'PORT')
SMTP_SERVER = config.get('mailing', 'SMTP_SERVER')


class Mailing:
    @classmethod
    def _generate_new_password(cls, length=8):
        return ''.join((secrets.choice(string.ascii_letters + string.digits) for _ in range(length)))

    @classmethod
    async def send_new_password(cls, receiver):
        new_password = cls._generate_new_password()
        message = MIMEText(f"Your new password: {new_password}")
        message['To'] = receiver
        message['From'] = MAIL_ADDRESS
        message['Subject'] = 'Reset password'
        async with aiosmtplib.SMTP(hostname=SMTP_SERVER, port=PORT, username=MAIL_ADDRESS, password=SMTP_PASSWORD,
                                   start_tls=True) as session:
            await session.sendmail(MAIL_ADDRESS, receiver, message.as_string())
        return new_password

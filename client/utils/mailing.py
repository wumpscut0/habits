import os
import secrets
from string import digits
from email.mime.text import MIMEText

import aiosmtplib
from aiosmtplib import SMTPException

from client.utils import config

MAIL_ADDRESS = os.getenv('ORGANIZATION_EMAIL')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
PORT = config.getint('mailing', 'PORT')
SMTP_SERVER = config.get('mailing', 'SMTP_SERVER')


class Mailing:
    @classmethod
    async def _generate_secret_key(cls):
        return ''.join((secrets.choice(digits) for _ in range(6)))

    @classmethod
    async def verify_email(cls, receiver):
        verify_code = await cls._generate_secret_key()
        message = MIMEText(f'Your verify code: {verify_code}')
        message['To'] = receiver
        message['From'] = MAIL_ADDRESS
        message['Subject'] = 'Verify email'
        async with aiosmtplib.SMTP(
                hostname=SMTP_SERVER,
                username=MAIL_ADDRESS,
                port=PORT,
                password=SMTP_PASSWORD,
                use_tls=True
        ) as connect:
            try:
                await connect.sendmail(MAIL_ADDRESS, receiver, message.as_string())
            except SMTPException:
                return

            return verify_code

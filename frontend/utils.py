import os
import pickle
import secrets
from string import digits
from base64 import b64decode
import aiosmtplib
from email.mime.text import MIMEText

SMTP_SERVER = 'smtp.mail.ru'
MAIL_ADDRESS = os.getenv('ORGANIZATION_MAIL')
PORT = 465
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')


async def deserialize(sequence: str):
    return pickle.loads(b64decode(sequence.encode()))


async def generate_secret_key():
    return ''.join((secrets.choice(digits) for _ in range(6)))


async def verify_email(receiver):
    verify_code = generate_secret_key()
    message = MIMEText(f'Your verify code: {verify_code}')
    message['To'] = receiver
    message['From'] = MAIL_ADDRESS
    message['Subject'] = 'Verify email'
    async with aiosmtplib.SMTP(hostname=SMTP_SERVER, username=MAIL_ADDRESS, port=PORT, password=SMTP_PASSWORD,
                               start_tls=True) as session:
        await session.sendmail(MAIL_ADDRESS, receiver, message.as_string())
    return verify_code

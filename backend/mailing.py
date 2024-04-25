import os
import aiosmtplib
import secrets
import string
from email.mime.text import MIMEText

SMTP_SERVER = 'smtp.mail.ru'
MAIL_ADDRESS = os.getenv('ORGANIZATION_MAIL')
PORT = 465
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')


def generate_new_password(length=8):
    return ''.join((secrets.choice(string.ascii_letters + string.digits) for _ in range(length)))


async def send_new_password(receiver):
    new_password = generate_new_password()
    message = MIMEText(f"Your new password: {new_password}")
    message['To'] = receiver
    message['From'] = MAIL_ADDRESS
    message['Subject'] = 'Reset password'
    async with aiosmtplib.SMTP(hostname=SMTP_SERVER, port=PORT, username=MAIL_ADDRESS, password=SMTP_PASSWORD, start_tls=True) as session:
        await session.sendmail(MAIL_ADDRESS, receiver, message.as_string())
    return new_password

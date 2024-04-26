import os
import jwt
from passlib.handlers.pbkdf2 import pbkdf2_sha256

from backend.database import Session
from backend.routers.models import Auth, TelegramId, UpdatePassword
from backend.database.queries import authorization, update_password, sign_up, get_user, get_user_email, \
    invert_user_notifications
from fastapi import FastAPI, Header, HTTPException
from typing import Annotated
from backend.mailing import send_new_password

from backend.routers.utils import verify_password

app = FastAPI()


@app.post("/sign_up")
async def sign_up_(sign_up__: TelegramId):
    async with Session.begin() as session:
        await sign_up(session, **sign_up__.model_dump())


@app.post("/sign_in")
async def sign_in(auth: Auth):
    async with Session.begin() as session:
        user = await get_user(session, auth.telegram_id)
        if user.hash is not None and auth.hash is None:
            raise HTTPException(400, 'Give me hash')
        elif user.hash is not None and auth.password:
            await verify_password(auth.password, user.hash)

        return jwt.encode(auth.model_dump(), os.getenv('JWT'))


@app.patch('/update_password')
async def update_password_(update_password__: UpdatePassword, Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        await authorization(session, Authorization)
        await update_password(session, **update_password__.model_dump())





@app.patch("/reset_password")
async def get_mail(telegram_id: TelegramId):
    async with Session.begin() as session:
        email = await get_user_email(session, telegram_id.telegram_id)
        if email is None:
            raise HTTPException(404, 'User not found')
        new_password = await send_new_password(email)
        hash_ = pbkdf2_sha256.hash(new_password)
        await update_password(session, telegram_id.telegram_id, hash_)
        return email


@app.patch("/invert_notification")
async def invert_notification(telegram_id: TelegramId):
    async with Session.begin() as session:
        return await invert_user_notifications(session, telegram_id.telegram_id)




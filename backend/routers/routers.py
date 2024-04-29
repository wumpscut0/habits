import os
import jwt
from passlib.handlers.pbkdf2 import pbkdf2_sha256

from backend.database import Session
from backend.routers.models import Auth, TelegramId, UpdatePassword, HabitM
from backend.database.queries import AuthQ, HabitsQ, UserDataQ
from fastapi import FastAPI, Header, HTTPException, Request
from typing import Annotated
from backend.mailing import send_new_password

from backend.routers.utils import verify_password
from loggers import errors

app = FastAPI()


@app.post("/sign_up")
async def sign_up_(sign_up__: TelegramId):
    async with Session.begin() as session:
        await sign_up(session, **sign_up__.model_dump())


@app.post("/sign_in")
async def authorization(auth: Auth):
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
        telegram_id = await AuthQ.authentication(session, Authorization)
        await UserDataQ.update_password(session, telegram_id, update_password__.hash)
        if update_password__.email is not None:
            await UserDataQ.update_email(session, telegram_id, update_password__.email)


@app.patch("/reset_password")
async def reset_password(telegram_id: TelegramId):
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


@app.get('/show_up')
async def show_up(Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        telegram_id = await AuthQ.authentication(session, Authorization)
        return await HabitsQ.get_user_habits(session, telegram_id)


@app.get("/has_a_mail")
async def has_a_mail(Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        telegram_id = await AuthQ.authentication(session, Authorization)
        return {
            "email": UserDataQ.get_user_email(session, telegram_id.telegram_id)
        }


@app.get('/is_name_using')
async def is_name_using(name: str, Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        telegram_id = await AuthQ.authentication(session, Authorization)
        await HabitsQ.is_name_using(session,  telegram_id, name)


@app.post('/create_habit')
async def create_habit(habit: HabitM, Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        telegram_id = await AuthQ.authentication(session, Authorization)
        await HabitsQ.create(session, habit)


@app.middleware('http')
async def error_abyss(request: Request, call_next):
    try:
        return call_next(request)
    except Exception as e:
        errors.error(e)
        raise HTTPException(500, e)







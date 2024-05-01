from typing import Annotated

from fastapi import Header, Request

from backend import errors
from backend.database.queries import *
from backend.database import Session
from backend.routers import Mailing, app
from backend.routers.models import AuthApiModel, TelegramIdApiModel, UpdatePasswordApiModel, HabitApiModel
from backend.database.queries import AuthQueries, HabitsQueries, CommonQueries, decode_jwt


@app.post("/sign_up")
async def registration(telegram_id_api_model: TelegramIdApiModel):
    async with Session.begin() as session:
        await AuthQueries.registration(session, **telegram_id_api_model.model_dump())


@app.post("/sign_in")
async def authorization(auth_api_model: AuthApiModel):
    async with Session.begin() as session:
        await AuthQueries.authorisation(session, **auth_api_model.model_dump())


@app.patch('/update_password')
async def update_password_(update_password_api_model: UpdatePasswordApiModel, Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        telegram_id = await AuthQueries.authentication(session, Authorization)
        await CommonQueries.update_password(session, telegram_id, update_password_api_model.hash)
        if update_password_api_model.email is not None:
            await CommonQueries.update_email(session, telegram_id, update_password_api_model.email)


@app.patch("/reset_password")
async def reset_password(Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        telegram_id = await AuthQueries.authentication(session, Authorization)
        email = await CommonQueries.get_user_email(session, telegram_id)
        if email is None:
            raise HTTPException(404, 'User not found')
        new_password = await Mailing.send_new_password(email)
        hash_ = pbkdf2_sha256.hash(new_password)
        await CommonQueries.update_password(session, telegram_id, hash_)
        return email


@app.patch("/invert_notification")
async def invert_notification(telegram_id_api_model: TelegramIdApiModel):
    async with Session.begin() as session:
        return await CommonQueries.invert_user_notifications(session, **telegram_id_api_model.model_dump())


@app.get('/show_up_habits')
async def show_up(Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        telegram_id = await AuthQueries.authentication(session, Authorization)
        return await HabitsQueries.get_user_habits(session, telegram_id)


@app.get("/has_a_mail")
async def has_a_mail(Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        telegram_id = await AuthQueries.authentication(session, Authorization)
        return {
            "email": CommonQueries.get_user_email(session, telegram_id.telegram_id)
        }


@app.post('/create_target')
async def create_habit(habit_api_model: HabitApiModel, Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        telegram_id = await AuthQueries.authentication(session, Authorization)
        await HabitsQueries.create(session, telegram_id, **habit_api_model.model_dump())


@app.patch('/update_habit_name/{habit_id}')
async def update_habit_name(habit_id: int, name: str, Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        telegram_id = await AuthQueries.authentication(session, Authorization)
        await HabitsQueries.update_name(session, telegram_id, habit_id, name)


@app.patch('/update_habit_description/{habit_id}')
async def update_habit_description(habit_id: int, description: str, Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        telegram_id = await AuthQueries.authentication(session, Authorization)
        await HabitsQueries.update_description(session, telegram_id, habit_id, description)


@app.delete('/delete_habit/{habit_id}')
async def delete_habit(habit_id: int, Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        await AuthQueries.authentication(session, Authorization)
        await HabitsQueries.delete(session, habit_id)


@app.patch('/invert_habit_completed/{habit_id}')
async def invert_habit_completed(habit_id: int, Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        telegram_id = await AuthQueries.authentication(session, Authorization)
        return await HabitsQueries.invert_completed(session, telegram_id, habit_id)


@app.patch('/increase_habits_progress/{key}')
async def increase_habits_progress(key: str):
    if os.getenv('SERVICES_PASSWORD') != (await decode_jwt(key))['password']:
        raise HTTPException(401)
    async with Session.begin() as session:
        await HabitsQueries.increase_progress(session)


@app.middleware('http')
async def error_abyss(request: Request, call_next):
    try:
        return call_next(request)
    except Exception as e:
        errors.error(e)
        raise HTTPException(500)








from typing import Annotated

from fastapi import Header, Request


from backend import errors
from backend.database.queries import *
from backend.database import Session
from backend.routers import Mailing, app
from backend.routers.models import AuthApiModel, TelegramIdApiModel, UpdatePasswordApiModel, HabitApiModel
from backend.database.queries import AuthQueries, TargetsQueries, CommonQueries, decode_jwt


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


@app.patch("/invert_notification/{key}/{user_id}")
async def invert_notification(key: str, user_id: int):
    if os.getenv('SERVICES_PASSWORD') != (await decode_jwt(key))['password']:
        raise HTTPException(401)
    async with Session.begin() as session:
        return await CommonQueries.invert_user_notifications(session, user_id)


@app.get("/notification_time")
async def get_notification_time(Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        telegram_id = await AuthQueries.authentication(session, Authorization)
        time = await CommonQueries.user_notification_time(session, telegram_id)
        return {
            "hour": time.hour,
            "minute": time.minute
        }


@app.patch("notification_time")
async def change_notification_time(Authorization: Annotated[str: Header()]):
    async with Session.begin() as session:
        telegram_id = await AuthQueries.authentication(session, Authorization)



@app.get('/show_up_targets')
async def show_up(Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        telegram_id = await AuthQueries.authentication(session, Authorization)
        return await TargetsQueries.get_user_targets(session, telegram_id)


@app.get("/has_a_mail")
async def has_a_mail(Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        telegram_id = await AuthQueries.authentication(session, Authorization)
        return {
            "email": CommonQueries.get_user_email(session, telegram_id.telegram_id)
        }


@app.post('/create_target')
async def create_target(target_api_model: HabitApiModel, Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        telegram_id = await AuthQueries.authentication(session, Authorization)
        await TargetsQueries.create(session, telegram_id, **target_api_model.model_dump())


@app.patch('/update_target_name/{target_id}')
async def update_target_name(target_id: int, name: str, Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        telegram_id = await AuthQueries.authentication(session, Authorization)
        await TargetsQueries.update_name(session, telegram_id, target_id, name)


@app.patch('/update_target_description/{target_id}')
async def update_target_description(target_id: int, description: str, Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        telegram_id = await AuthQueries.authentication(session, Authorization)
        await TargetsQueries.update_description(session, telegram_id, target_id, description)


@app.delete('/delete_target/{target_id}')
async def delete_target(target_id: int, Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        await AuthQueries.authentication(session, Authorization)
        await TargetsQueries.delete(session, target_id)


@app.patch('/invert_target_completed/{target_id}')
async def invert_target_completed(target_id: int, Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        telegram_id = await AuthQueries.authentication(session, Authorization)
        return await TargetsQueries.invert_completed(session, telegram_id, target_id)
    

@app.get('/is_all_done')
async def is_all_done(Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        telegram_id = await AuthQueries.authentication(session, Authorization)
        return await TargetsQueries.is_all_done(session, telegram_id)


@app.patch('/increase_targets_progress/{key}')
async def increase_targets_progress(key: str):
    if os.getenv('SERVICES_PASSWORD') != (await decode_jwt(key))['password']:
        raise HTTPException(401)
    async with Session.begin() as session:
        await TargetsQueries.increase_progress(session)


@app.get('/users_ids/{key}')
async def increase_targets_progress(key: str):
    if os.getenv('SERVICES_PASSWORD') != (await decode_jwt(key))['password']:
        raise HTTPException(401)
    async with Session.begin() as session:
        return await CommonQueries.users_ids(session)


@app.middleware('http')
async def error_abyss(request: Request, call_next):
    try:
        return call_next(request)
    except Exception as e:
        errors.error(e)
        raise HTTPException(500)







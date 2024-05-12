import os
from typing import Annotated
from datetime import time, UTC
from fastapi import Header, Request, FastAPI, HTTPException
from starlette.responses import PlainTextResponse

from backend.database import Session
from backend.routers.models import AuthApiModel, TelegramIdApiModel, UpdatePasswordApiModel, TargetApiModel, \
    NotificationTimeApiModel, UpdateEmailApiModel
from backend.database.queries import AuthQueries, TargetsQueries, CommonQueries
from backend.utils import decode_jwt
from backend.utils.loggers import errors

app = FastAPI()


@app.post("/sign_up")
async def registration(telegram_id_api_model: TelegramIdApiModel):
    async with Session.begin() as session:
        await AuthQueries.registration(session, **telegram_id_api_model.model_dump())


@app.post("/sign_in", response_class=PlainTextResponse)
async def authorization(auth_api_model: AuthApiModel):
    async with Session.begin() as session:
        return await AuthQueries.authorisation(session, **auth_api_model.model_dump())


########################################################################################################################


@app.get('/is_password_set/{user_id}', response_class=PlainTextResponse)
async def is_password_set(user_id: str):
    data = await decode_jwt(user_id)
    async with Session.begin() as session:
        if await CommonQueries.is_password_set(session, data["telegram_id"]) is not None:
            return "1"
        return "0"


@app.patch('/update_password/{jwt}')
async def update_password(jwt: str):
    data = await decode_jwt(jwt)
    data = UpdatePasswordApiModel.model_validate(data)
    async with Session.begin() as session:
        await CommonQueries.update_password(session, **data.model_dump())


# @app.patch("/reset_password/{user_id}")
# async def reset_password(user_id):
#     data = await decode_jwt(user_id)
#     async with Session.begin() as session:
#         email = await CommonQueries.get_user_email(session, data["telegram_id"])
#         if email is None:
#             raise HTTPException(404, 'User not found')
#         return await Mailing.verify_email(email)


@app.delete("/delete_password")
async def delete_password(Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        telegram_id = await AuthQueries.authentication(session, Authorization)
        await CommonQueries.delete_password(session, telegram_id)


########################################################################################################################


@app.get('/is_email_set/{user_id}', response_class=PlainTextResponse)
async def is_email_set(user_id: str):
    data = await decode_jwt(user_id)
    async with Session.begin() as session:
        if await CommonQueries.is_email_set(session, data["telegram_id"]) is not None:
            return "1"
        return "0"


@app.patch('/update_email')
async def update_email(update_password_api_model: UpdateEmailApiModel, Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        telegram_id = await AuthQueries.authentication(session, Authorization)
        await CommonQueries.update_email(session, telegram_id, update_password_api_model.email)


@app.delete("/delete_email")
async def delete_password(Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        telegram_id = await AuthQueries.authentication(session, Authorization)
        await CommonQueries.delete_email(session, telegram_id)


@app.get("/get_user_email/{user_id}", response_class=PlainTextResponse)
async def get_user_email(user_id: str):
    data = await decode_jwt(user_id)
    async with Session.begin() as session:
        email = await CommonQueries.get_user_email(session, data["telegram_id"])
        if email is None:
            raise HTTPException(404)
        return email


########################################################################################################################


@app.patch("/invert_notifications/{user_id}")
async def invert_notification(user_id: str):
    data = await decode_jwt(user_id)
    async with Session.begin() as session:
        return await CommonQueries.invert_user_notifications(session, data["telegram_id"])


@app.get("/notification_time/{user_id}")
async def get_notification_time(user_id: str):
    data = await decode_jwt(user_id)
    async with Session.begin() as session:
        time_ = await CommonQueries.user_notification_time(session, data["telegram_id"])
        return {
            "hour": time_.hour,
            "minute": time_.minute
        }


@app.get("/notification_is_on/{user_id}")
async def notification_is_on(user_id: str):
    data = await decode_jwt(user_id)
    async with Session.begin() as session:
        if await CommonQueries.notification_is_on(session, data["telegram_id"]):
            return 1
        return 0


@app.patch("/notification_time")
async def change_notification_time(time_: NotificationTimeApiModel, Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        telegram_id = await AuthQueries.authentication(session, Authorization)
        await CommonQueries.update_notification_time(session, telegram_id, time(**time_.model_dump(), tzinfo=UTC))
        time_ = await CommonQueries.user_notification_time(session, telegram_id)
        return {
            "hour": time_.hour,
            "minute": time_.minute
        }


########################################################################################################################


@app.get('/targets')
async def targets(Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        telegram_id = await AuthQueries.authentication(session, Authorization)
        t = await TargetsQueries.get_targets(session, telegram_id)
        print(t)
        return t

@app.get("/completed_targets")
async def get_completed_targets(Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        telegram_id = await AuthQueries.authentication(session, Authorization)
        return await TargetsQueries.get_completed_targets(session, telegram_id)


@app.get("/target/{target_id}")
async def get_target(target_id: int, Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        await AuthQueries.authentication(session, Authorization)
        return TargetsQueries.get_target(session, target_id)


@app.post('/create_target')
async def create_target(target_api_model: TargetApiModel, Authorization: Annotated[str, Header()]):
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


@app.get('/is_all_done/{user_id}')
async def notification_is_on(user_id: str):
    data = await decode_jwt(user_id)
    async with Session.begin() as session:
        return await TargetsQueries.is_all_done(session, data["telegram_id"])


@app.patch('/increase_targets_progress/{key}')
async def increase_targets_progress(key: str):
    if os.getenv('SERVICES_PASSWORD') != (await decode_jwt(key))['password']:
        raise HTTPException(401)
    async with Session.begin() as session:
        return await TargetsQueries.increase_progress(session)


@app.get('/users_ids/{key}')
async def increase_targets_progress(key: str):
    if os.getenv('SERVICES_PASSWORD') != (await decode_jwt(key))['password']:
        raise HTTPException(401)
    async with Session.begin() as session:
        return await CommonQueries.users_ids(session)


@app.middleware('http')
async def error_abyss(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        errors.error(e)
        raise HTTPException(500, e)

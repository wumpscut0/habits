from typing import Annotated
from datetime import time

from fastapi import Header, HTTPException
from starlette.responses import PlainTextResponse

from backend.database import Session
from backend.routers.models import UpdatePasswordApiModel, NotificationTimeApiModel, AuthApiModel, EmailApiModel, \
    UserIdApiModel
from backend.database.queries import PasswordQueries, EmailQueries, NotificationsQueries, UserQueries
from backend.routers import app, Authority


@app.post("/users")
async def registration(user_id_api_model: UserIdApiModel, Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        await Authority.service_authentication(Authorization)
        user_id = user_id_api_model.user_id
        await UserQueries.registration(session, user_id)


@app.post("/users/login", response_class=PlainTextResponse)
async def user_auth(auth_api_model: AuthApiModel, Authorization: Annotated[str, Header()]):
    await Authority.service_authentication(Authorization)
    return await Authority.user_authorization(**auth_api_model.model_dump())


@app.get('/users/{user_id}')
async def get_user(user_id: str, Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        await Authority.service_authentication(Authorization)
        user_id = await Authority.decrypt_message(user_id)
        try:
            user_id = int(await Authority.decrypt_message(user_id))
        except ValueError:
            raise HTTPException(400, "User id must be integer")
        return await UserQueries.get_user(session, user_id)


@app.get('/users')
async def get_user(Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        await Authority.service_authentication(Authorization)
        return await UserQueries.get_users(session)


@app.put('/users/password')
async def update_password(data: UpdatePasswordApiModel, Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        await Authority.service_authentication(Authorization)
        await PasswordQueries.update_password(session, **data.model_dump())


@app.delete("/users/password")
async def delete_password(Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        user = await Authority.user_authentication(Authorization)
        await PasswordQueries.delete_password(session, user.user_id)


@app.put('/users/email')
async def update_email(email_api_model: EmailApiModel, Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        user = await Authority.user_authentication(Authorization)
        await EmailQueries.update(session, user.user_id, email_api_model.email)


@app.delete("/users/email")
async def delete_email(Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        user = await Authority.user_authentication(Authorization)
        await EmailQueries.delete(session, user.user_id)


@app.patch("/users/notifications/invert")
async def invert_notifications(user_id_api_model: UserIdApiModel, Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        await Authority.service_authentication(Authorization)
        await NotificationsQueries.invert(session, user_id_api_model.user_id)


@app.put("/users/notification/time")
async def change_notification_time(time_: NotificationTimeApiModel, Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        user = await Authority.user_authentication(Authorization)
        await NotificationsQueries.update(session, user.user_id, time(**time_.model_dump()))

from typing import Annotated
from datetime import time

from fastapi import Depends, APIRouter
from starlette.responses import JSONResponse

from server.database import Session
from server.api.models import (
    UpdatePasswordApiModel,
    NotificationTimeApiModel,
    EmailApiModel,
    Token,
    UserApiModel,
    Payload,
    UserIdApiModel,
)
from server.database.queries import (
    PasswordQueries,
    EmailQueries,
    NotificationsQueries,
    UserQueries,
)
from server.api import Authority

users_router = APIRouter(prefix="/users")


@users_router.post("/", status_code=201)
async def registration(user_api_model: UserApiModel):
    async with Session.begin() as session:
        await UserQueries.registration(session, user_api_model)


@users_router.post("/login")
async def user_auth(token: Annotated[Token, Depends(Authority.user_authenticate)]):
    return token


@users_router.get("/{user_id}")
async def get_user(user_id: str):
    async with Session.begin() as session:
        return await UserQueries.get_user(
            session, (await Authority.decrypt_message(user_id)).decode()
        )


@users_router.get("/")
async def get_users():
    async with Session.begin() as session:
        return await UserQueries.get_users(session)


@users_router.put("/password")
async def update_password(update_password_api_model: UpdatePasswordApiModel):
    async with Session.begin() as session:
        await PasswordQueries.update_password(session, update_password_api_model)


@users_router.delete("/password")
async def delete_password(
    payload: Annotated[Payload, Depends(Authority.user_authorization)]
):
    async with Session.begin() as session:
        await PasswordQueries.delete_password(session, payload["sub"])


@users_router.put("/email", status_code=201)
async def update_email(
    email_api_model: EmailApiModel,
    payload: Annotated[Payload, Depends(Authority.user_authorization)],
):
    async with Session.begin() as session:
        await EmailQueries.update(session, payload["sub"], email_api_model.email)


@users_router.delete("/email")
async def delete_email(
    payload: Annotated[Payload, Depends(Authority.user_authorization)]
):
    async with Session.begin() as session:
        await EmailQueries.delete(session, payload["sub"])


@users_router.patch("/notifications")
async def invert_notifications(user_id_api_model: UserIdApiModel):
    async with Session.begin() as session:
        await NotificationsQueries.invert(session, user_id_api_model.user_id)


@users_router.put("/notifications")
async def change_notification_time(
    time_: NotificationTimeApiModel,
    payload: Annotated[Payload, Depends(Authority.user_authorization)],
):
    async with Session.begin() as session:
        await NotificationsQueries.update(
            session, payload["sub"], time(**time_.model_dump())
        )

import os

import jwt
from sqlalchemy import update, insert, select, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from passlib.handlers.pbkdf2 import pbkdf2_sha256

from backend.database import verify_password, decode_jwt
from backend.database.models import UserORM, TargetORM
from backend.routers.models import AuthApiModel, HabitApiModel


class AuthQueries:
    @staticmethod
    async def registration(session: AsyncSession, telegram_id: int):
        try:
            await session.execute(insert(UserORM).values({"telegram_id": telegram_id}))
            await session.commit()
        except IntegrityError:
            raise HTTPException(409, "User already exists")

    @staticmethod
    async def authorisation(session: AsyncSession, telegram_id: int, password: str | None = None):
        user = await CommonQueries.user(session, telegram_id)
        if user.hash is not None and password is None:
            raise HTTPException(400, 'Give me password')
        elif user.hash is not None and password:
            await verify_password(password, user.hash)

        return jwt.encode(AuthApiModel(telegram_id=telegram_id, password=password).model_dump(), os.getenv('JWT'))

    @staticmethod
    async def authentication(session: AsyncSession, token: str):
        data = AuthApiModel.model_validate(await decode_jwt(token))

        user = await CommonQueries.user(session, data.telegram_id)

        if user.hash is not None and not pbkdf2_sha256.verify(data.password, user.hash):
            raise HTTPException(
                status_code=401, detail="Wrong password"
            )
        return user.telegram_id


class CommonQueries:
    @staticmethod
    async def users_ids(session: AsyncSession):
        return (await session.execute(select(UserORM.telegram_id).where(UserORM.notifications))).scalars()

    @staticmethod
    async def user_notification_time(session: AsyncSession, telegram_id: int):
        return (await session.execute(select(UserORM.notification_time).where(UserORM.telegram_id == telegram_id))).scalar()

    @staticmethod
    async def change_notification_time(session: AsyncSession, telegram_id: int):
        await session.execute(update(UserORM.notification_time).values({"notification_time": time()}).where(UserORM.telegram_id == telegram_id))

    @staticmethod
    async def user(session: AsyncSession, telegram_id: int):
        user = await session.get(UserORM, ident=telegram_id)
        if user is None:
            raise HTTPException(
                status_code=404, detail="User not found"
            )
        return user

    @staticmethod
    async def get_user_email(session: AsyncSession, telegram_id: int):
        return (await session.execute(select(UserORM.email).where(UserORM.telegram_id == telegram_id))).scalar()

    @staticmethod
    async def update_password(session: AsyncSession, telegram_id: int, hash_: str):
        async with session.begin():
            await session.execute(update(UserORM).where(UserORM.telegram_id == telegram_id).values({"password": hash_}))

    @staticmethod
    async def update_email(session: AsyncSession, telegram_id: int, email: str):
        async with session.begin():
            await session.execute(update(UserORM).where(UserORM.telegram_id == telegram_id).values({"email": email}))

    @staticmethod
    async def invert_user_notifications(session: AsyncSession, telegram_id: int):
        async with session.begin():
            notifications = (
                await session.execute(select(UserORM.notifications).where(UserORM.telegram_id == telegram_id))).scalar()
            await session.execute(
                update(UserORM).where(UserORM.telegram_id == telegram_id).values({"notifications": not notifications})
            )
        return "1" if not notifications else '0'


class TargetsQueries:
    @staticmethod
    async def create(
        session: AsyncSession,
        telegram_id: int,
        name: str,
        description: str | None = None,
        border_progress: int | None = None
    ):
        await session.execute(insert(TargetORM).values({"user_id": telegram_id}, **HabitApiModel(
            name=name,
            description=description,
            border_progress=border_progress
        ).model_dump()))

    @staticmethod
    async def delete(
        session: AsyncSession,
        habit_id: int
    ):
        await session.execute(delete(TargetORM).where(TargetORM.id == habit_id))

    @staticmethod
    async def get_user_targets(session: AsyncSession, telegram_id: int):
        return [
            habit.as_dict_() for habit in (await session.execute(
                select(TargetORM)
                .filter(TargetORM.user_id == telegram_id, TargetORM.progress != TargetORM.border_progress)
            )).scalars()
        ]

    @staticmethod
    async def update_name(session: AsyncSession, telegram_id: int, habit_id: int, name: str):
        await session.execute(
            update(TargetORM)
            .values({'name': name})
            .filter(TargetORM.user_id == telegram_id, TargetORM.id == habit_id)
        )
        await session.commit()

    @staticmethod
    async def update_description(session: AsyncSession, telegram_id: int, habit_id: int, description: str):
        await session.execute(
            update(TargetORM)
            .values({'description': description})
            .filter(TargetORM.user_id == telegram_id, TargetORM.id == habit_id)
        )
        await session.commit()

    @staticmethod
    async def invert_completed(session: AsyncSession, telegram_id: int, habit_id: int):
        habit = (await session.execute(
            select(TargetORM.completed)
            .filter(TargetORM.user_id == telegram_id, TargetORM.id == habit_id)
        )).scalar()

        await session.execute(
            update(TargetORM)
            .values({'completed': not habit.completed})
            .filter(TargetORM.user_id == telegram_id, TargetORM.id == habit_id)

        )
        await session.commit()
        return '1' if habit.completed else '0'

    @staticmethod
    async def is_all_done(session: AsyncSession, telegram_id: int):
        return '1' if all((await session.execute(select(TargetORM.completed).where(UserORM.telegram_id == telegram_id)))
                          .scalars()) else '0'

    @staticmethod
    async def increase_progress(session: AsyncSession):
        await session.execute(update(TargetORM).values({"completed": False, "progress": TargetORM.progress + 1}).filter(
            TargetORM.progress + 1 <= TargetORM.border_progress, TargetORM.completed
        ))
        await session.commit()

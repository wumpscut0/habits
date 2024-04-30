import os
import jwt
import pydantic
from fastapi import HTTPException
from sqlalchemy import update, insert, select, and_, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.models import User, Habit
from backend.routers.models import Auth, HabitM
from passlib.hash import pbkdf2_sha256


async def decode_jwt(token: str):
    try:
        data = jwt.decode(token, key=os.getenv('JWT'), algorithms="HS256")
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=400, detail="Invalid jwt token"
        )
    except pydantic.ValidationError:
        raise HTTPException(
            status_code=422, detail="Validation error"
        )
    return data


class AuthQ:
    @staticmethod
    async def registration(session: AsyncSession, telegram_id: int):
        try:
            await session.execute(insert(User).values({"telegram_id": telegram_id}))
            await session.commit()
        except IntegrityError:
            raise HTTPException(409, "User already exists")

    @staticmethod
    async def authentication(session: AsyncSession, token: str):
        data = Auth.model_validate(await decode_jwt(token))

        user = await UserDataQ.user(session, data.telegram_id)

        if user.hash is not None and not pbkdf2_sha256.verify(data.password, user.hash):
            raise HTTPException(
                status_code=401, detail="Wrong password"
            )
        return user.telegram_id


class UserDataQ:
    @classmethod
    async def user(cls, session: AsyncSession, telegram_id: int):
        user = await session.get(User, ident=telegram_id)
        if user is None:
            raise HTTPException(
                status_code=404, detail="User not found"
            )
        return user

    @classmethod
    async def get_user_email(cls, session: AsyncSession, telegram_id: int):
        return (await session.execute(select(User.email).where(User.telegram_id == telegram_id))).scalar()

    @classmethod
    async def update_password(cls, session: AsyncSession, telegram_id: int, hash_: str):
        async with session.begin():
            await session.execute(update(User).where(User.telegram_id == telegram_id).values({"password": hash_}))

    @classmethod
    async def update_email(cls, session: AsyncSession, telegram_id: int, email: str):
        async with session.begin():
            await session.execute(update(User).where(User.telegram_id == telegram_id).values({"email": email}))

    @classmethod
    async def invert_user_notifications(cls, session: AsyncSession, telegram_id: int):
        async with session.begin():
            notifications = (
                await session.execute(select(User.notifications).where(User.telegram_id == telegram_id))).scalar()
            await session.execute(
                update(User).where(User.telegram_id == telegram_id).values({"notifications": not notifications}))
        return "1" if not notifications else '0'


class HabitsQ:
    @staticmethod
    async def create(
        session: AsyncSession,
        data: HabitM,
        telegram_id: int
    ):
        await session.execute(insert(Habit).values({"user_id": telegram_id}, **data.model_dump()))

    @staticmethod
    async def delete(
        session: AsyncSession,
        habit_id: int
    ):
        await session.execute(delete(Habit).where(Habit.id == habit_id))

    @staticmethod
    async def get_user_habits(session: AsyncSession, telegram_id: int):
        return [
            habit.as_dict_() for habit in (await session.execute(
                select(Habit)
                .filter(Habit.user_id == telegram_id, Habit.progress != Habit.border_progress)
            )).scalars()
        ]

    @staticmethod
    async def update_name(session: AsyncSession, telegram_id: int, habit_id: int, name: str):
        await session.execute(
            update(Habit)
            .values({'name': name})
            .filter(Habit.user_id == telegram_id, Habit.id == habit_id)
        )
        await session.commit()

    @staticmethod
    async def update_description(session: AsyncSession, telegram_id: int, habit_id: int, description: str):
        await session.execute(
            update(Habit)
            .values({'description': description})
            .filter(Habit.user_id == telegram_id, Habit.id == habit_id)
        )
        await session.commit()

    @staticmethod
    async def invert_completed(session: AsyncSession, telegram_id: int, habit_id: int):
        habit = (await session.execute(
            select(Habit.completed)
            .filter(Habit.user_id == telegram_id, Habit.id == habit_id)
        )).scalar()

        await session.execute(
            update(Habit)
            .values({'completed': not habit.completed})
            .filter(Habit.user_id == telegram_id, Habit.id == habit_id)

        )
        await session.commit()
        return '1' if habit.completed else '0'

    @staticmethod
    async def increase_progress(session: AsyncSession):
        await session.execute(update(Habit).filter(Habit.progress + 1 <= Habit.border_progress))
        await session.commit()

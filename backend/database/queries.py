import os
import jwt
import pydantic
from fastapi import HTTPException
from sqlalchemy import update, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import User
from backend.routers.models import Auth
from passlib.hash import pbkdf2_sha256


async def get_user(session: AsyncSession, telegram_id: int):
    user = await session.get(User, ident=telegram_id)
    if user is None:
        raise HTTPException(
            status_code=404, detail="User not found"
        )
    return user


async def sign_up(session: AsyncSession, telegram_id: int):
    try:
        await session.execute(insert(User).values({"telegram_id": telegram_id}))
        await session.commit()
    except IntegrityError:
        raise HTTPException(409, "User already exists")


async def authorization(session: AsyncSession, token: str):
    try:
        data = jwt.decode(token, key=os.getenv('JWT'), algorithms="HS256")
        data = Auth.model_validate(data)
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=400, detail="Invalid jwt token"
        )
    except pydantic.ValidationError:
        raise HTTPException(
            status_code=422, detail="Validation error"
        )

    user = await get_user(session, data.telegram_id)

    if user.hash is not None and not pbkdf2_sha256.verify(data.password, user.hash):
        raise HTTPException(
            status_code=401, detail="Wrong password"
        )


async def update_password(session: AsyncSession, telegram_id: int, hash_: str):
    async with session.begin():
        await session.execute(update(User).where(User.telegram_id == telegram_id).values({"password": hash_}))

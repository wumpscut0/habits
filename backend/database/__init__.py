import os

import jwt
import pydantic
from fastapi import HTTPException
from passlib.handlers.pbkdf2 import pbkdf2_sha256
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from dotenv import load_dotenv, find_dotenv

from backend.database.models import Base

load_dotenv(find_dotenv())

engine = create_async_engine(os.getenv('DATABASE'))
Session = async_sessionmaker(engine, expire_on_commit=False)


async def create_all():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata)


async def verify_password(password: str, hash_):
    if not pbkdf2_sha256.verify(password, hash_):
        raise HTTPException(
            status_code=401, detail="Wrong password"
        )


async def decode_jwt(token: str):
    try:
        data = jwt.decode(token, key=os.getenv('JWT'), algorithms="HS256")
        return data
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=400, detail="Invalid jwt token"
        )
    except pydantic.ValidationError:
        raise HTTPException(
            status_code=422, detail="Validation error"
        )

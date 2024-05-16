import os
from contextlib import asynccontextmanager
from typing import Dict
from datetime import datetime, timedelta

import jwt
import pydantic
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.twofactor import InvalidToken
from fastapi import Request, FastAPI, HTTPException
from jwt import ExpiredSignatureError
from passlib.handlers.pbkdf2 import pbkdf2_sha256

from server.database import Session, create_all
from server.database.queries import UserQueries
from server.api.models import AuthApiModel, UpdatePasswordApiModel, TargetApiModel, NotificationTimeApiModel
from server.utils.loggers import errors

app = FastAPI()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_all()
    yield


class Authority:
    _jwt_algorithm = "HS256"
    _cipher = Fernet(os.getenv('CIPHER'))

    @classmethod
    async def decrypt_message(cls, data: str):
        try:
            return cls._cipher.decrypt(data)
        except (InvalidToken, Exception):
            HTTPException(400)

    @classmethod
    async def _encode_jwt(cls, payload: Dict):
        return jwt.encode(payload=payload, algorithm=cls._jwt_algorithm)

    @classmethod
    async def _decode_jwt(cls, token: str):
        try:
            return jwt.decode(token, key=os.getenv('JWT'), algorithms=cls._jwt_algorithm)
        except ExpiredSignatureError:
            raise HTTPException(
                419, detail="Expired token"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=401, detail="Invalid jwt token"
            )
        except pydantic.ValidationError:
            raise HTTPException(
                status_code=401, detail="Validation error"
            )

    @classmethod
    async def _verify_password(cls, password: str, hash_):
        if not pbkdf2_sha256.verify(password, hash_):
            raise HTTPException(
                status_code=401, detail="Wrong password"
            )

    @classmethod
    async def user_authentication(cls, user_id: int, password: str | None = None):
        async with Session.begin() as session:
            user = await UserQueries.get_user(session, user_id)
            if user.hash is not None:
                await cls._verify_password(password, user.hash)

        return jwt.encode({"password": password, "user_id": user_id}, os.getenv('JWT'))

    @classmethod
    async def user_authorization(cls, token):
        return AuthApiModel.model_validate(await cls._decode_jwt(token))

    @classmethod
    async def service_authentication(cls, password: str):
        await cls._verify_password(password, os.getenv('SERVICE_PASSWORD'))
        return await cls._encode_jwt(
            {
                "password": password,
                'exp': datetime.now() + timedelta(minutes=10)
            }
        )

    @classmethod
    async def service_authorization(cls, token):
        return await cls._decode_jwt(token)


@app.middleware('http')
async def error_abyss(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        errors.critical(f"{call_next.__name__}\n{e}")
        raise HTTPException(500, "Internal server error")

import os
from configparser import ConfigParser

import jwt
import pydantic
from fastapi import HTTPException
from passlib.handlers.pbkdf2 import pbkdf2_sha256


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

config = ConfigParser()

config.read(os.path.abspath(os.path.join(os.path.dirname(__file__), "config.ini")))

import os
from datetime import datetime, timedelta
from typing import Dict, Annotated

import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.twofactor import InvalidToken
from fastapi import HTTPException, Depends, Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.handlers.pbkdf2 import pbkdf2_sha256
from starlette import status

from server.api.models import AuthApiModel, Token
from server.database import Session
from server.database.queries import UserQueries, ServiceQueries
from server.utils import config

oauth2_schema = OAuth2PasswordBearer(tokenUrl="users/login")

ACCESS_TOKEN_EXPIRE_MINUTES = config.getint("limitations", "ACCESS_TOKEN_EXPIRE_MINUTES")


class Authority:
    _jwt_algorithm = "HS256"
    _cipher = Fernet(os.getenv('CIPHER'))

    @classmethod
    async def decrypt_message(cls, data: bytes | str):
        try:
            return cls._cipher.decrypt(data)
        except (InvalidToken, Exception):
            HTTPException(400)

    @classmethod
    def _encode_jwt(cls, payload: Dict):
        return jwt.encode(payload, os.getenv("JWT"), algorithm=cls._jwt_algorithm)

    @classmethod
    async def _decode_jwt(cls, token: str):
        try:
            return jwt.decode(token, key=os.getenv('JWT'), algorithms=cls._jwt_algorithm)
        except jwt.PyJWTError:
            HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @classmethod
    async def _verify_password(cls, password: str, hash_):
        return pbkdf2_sha256.verify(password, hash_)

    @classmethod
    async def user_authenticate(cls, auth_api_model: AuthApiModel):
        async with Session.begin() as session:
            user = await UserQueries.get_user(session, auth_api_model.user_id)
            if user is None or (user.get("hash") is not None and not await cls._verify_password(auth_api_model.password, user.get("hash"))):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect user id or api key",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        return Token(
            access_token=cls._encode_jwt({"sub": auth_api_model.user_id, "exp": expire}),
            token_type="bearer"
        )

    @classmethod
    async def user_authorization(cls, token: Annotated[str, Depends(oauth2_schema)]):
        payload = await cls._decode_jwt(token)
        async with Session.begin() as session:
            if UserQueries.get_user(session, payload.get("sub")) is None:
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect sub field")
        return payload

    @classmethod
    async def authenticate_service(cls, x_service_name: Annotated[str, Header()], api_key: Annotated[str, Header()]):
        async with Session.begin() as session:
            service = await ServiceQueries.get_service(session, x_service_name)
        if service is None or service.api_key != api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect service name or api key",
                headers={"WWW-Authenticate": "Bearer"},
            )

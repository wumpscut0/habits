import re
from typing import Optional

from fastapi import HTTPException
from pydantic import BaseModel
from pydantic_async_validation import AsyncValidationModelMixin
from pydantic_async_validation.validators import async_field_validator

from server.utils import config

MAX_PASSWORD_LENGTH = config.getint('limitations', "MAX_PASSWORD_LENGTH")
MAX_EMAIL_LENGTH = config.getint('limitations', "MAX_EMAIL_LENGTH")
MAX_NAME_LENGTH = config.getint("limitations", "MAX_NAME_LENGTH")
MAX_DESCRIPTION_LENGTH = config.getint('limitations', "MAX_DESCRIPTION_LENGTH")
MIN_BORDER_RANGE = config.getint('limitations', "MIN_BORDER_RANGE")
MAX_BORDER_RANGE = config.getint('limitations', "MAX_BORDER_RANGE")
ID_MAX_LENGTH = config.getint('limitations', "ID_MAX_LENGTH")


class Payload(BaseModel):
    sub: str
    exp: int


class Token(BaseModel):
    access_token: str
    token_type: str = "Bearer"


class UserIdApiModel(BaseModel):
    user_id: str

    @async_field_validator('user_id')
    async def user_id_validate(self, value: str):
        if len(value) > ID_MAX_LENGTH:
            raise HTTPException(
                400,
                detail=f'Maximum id length is {ID_MAX_LENGTH}'
            )


class UserApiModel(BaseModel):
    user_id: str
    hash: str | None = None
    email: str | None = None

    @async_field_validator('email')
    async def email_validate(self, value: str):
        if value is not None:
            if len(value) > MAX_EMAIL_LENGTH:
                raise HTTPException(
                    400,
                    detail=f'Maximum email length is {MAX_EMAIL_LENGTH}'
                )
            if not re.fullmatch(r'[a-zA-Z0-9]+@[a-zA-Z]+\.[a-zA-Z]+', value):
                raise HTTPException(
                    400,
                    detail=f'Invalid email format'
                )

    @async_field_validator('user_id')
    async def user_id_validate(self, value: str):
        if len(value) > ID_MAX_LENGTH:
            raise HTTPException(
                400,
                detail=f'Maximum id length is {ID_MAX_LENGTH}'
            )


class PasswordApiModel(AsyncValidationModelMixin, BaseModel):
    password: str

    @async_field_validator('password')
    async def password_validate(self, value: str):
        if len(value) > MAX_PASSWORD_LENGTH:
            raise HTTPException(
                400,
                detail=f'Maximum password length is {MAX_PASSWORD_LENGTH}'
            )


class EmailApiModel(AsyncValidationModelMixin, BaseModel):
    email: str

    @async_field_validator('email')
    async def email_validate(self, value: str):
        if len(value) > MAX_EMAIL_LENGTH:
            raise HTTPException(
                400,
                detail=f'Maximum email length is {MAX_EMAIL_LENGTH}'
            )
        if not re.fullmatch(r'[a-zA-Z0-9]+@[a-zA-Z]+\.[a-zA-Z]', value):
            raise HTTPException(
                400,
                detail=f'Invalid email format'
            )


class AuthApiModel(BaseModel):
    user_id: str
    password: Optional[str] = None

    @async_field_validator('user_id')
    async def user_id_validate(self, value: str):
        if len(value) > ID_MAX_LENGTH:
            raise HTTPException(
                400,
                detail=f'Maximum id length is {ID_MAX_LENGTH}'
            )

    @async_field_validator('password')
    async def password_validate(self, value: str):
        if len(value) > MAX_PASSWORD_LENGTH:
            raise HTTPException(
                400,
                detail=f'Maximum password length is {MAX_PASSWORD_LENGTH}'
            )


class UpdatePasswordApiModel(BaseModel):
    user_id: str
    hash: str

    @async_field_validator('user_id')
    async def user_id_validate(self, value: str):
        if len(value) > ID_MAX_LENGTH:
            raise HTTPException(
                400,
                detail=f'Maximum id length is {ID_MAX_LENGTH}'
            )


class TargetNameApiModel(AsyncValidationModelMixin, BaseModel):
    name: str

    @async_field_validator("name")
    async def name_validate(self, value):
        if len(value) > MAX_NAME_LENGTH:
            raise HTTPException(
                400,
                f"Max name length is {MAX_NAME_LENGTH}"
            )


class TargetDescriptionApiModel(AsyncValidationModelMixin, BaseModel):
    description: str

    @async_field_validator("description")
    async def description_validate(self, value: str):
        if len(value) > MAX_DESCRIPTION_LENGTH:
            raise HTTPException(
                400,
                f"Max name length is {MAX_DESCRIPTION_LENGTH}"
            )


class TargetApiModel(AsyncValidationModelMixin, BaseModel):
    name: str
    border_progress: int | None = None
    description: str | None = None

    @async_field_validator("name")
    async def name_validate(self, value):
        if len(value) > MAX_NAME_LENGTH:
            raise HTTPException(
                400,
                f"Max name length is {MAX_NAME_LENGTH}"
            )

    @async_field_validator("border_progress")
    async def border_validate(self, value: int):
        if value is not None:
            if not MIN_BORDER_RANGE <= value <= MAX_BORDER_RANGE:
                raise HTTPException(
                    400,
                    detail=f'Days for completed target must be in range {MIN_BORDER_RANGE} to {MAX_BORDER_RANGE}'
                )

    @async_field_validator("description")
    async def description_validate(self, value: str):
        if len(value) > MAX_DESCRIPTION_LENGTH:
            raise HTTPException(
                400,
                f"Max name length is {MAX_DESCRIPTION_LENGTH}"
            )


class UpdateTargetApiModel(BaseModel):
    name: str | None = None
    description: str | None = None

    @async_field_validator("name")
    async def name_validate(self, value):
        if value is not None and len(value) > MAX_NAME_LENGTH:
            raise HTTPException(
                400,
                f"Max name length is {MAX_NAME_LENGTH}"
            )

    @async_field_validator("description")
    async def description_validate(self, value: str):
        if value is not None and len(value) > MAX_DESCRIPTION_LENGTH:
            raise HTTPException(
                400,
                f"Max name length is {MAX_DESCRIPTION_LENGTH}"
            )


class NotificationTimeApiModel(AsyncValidationModelMixin, BaseModel):
    hour: int
    minute: int

    @async_field_validator('hour')
    async def hour_validate(self, value: int):
        if not 0 <= value <= 23:
            raise HTTPException(
                400,
                detail=f'Hour must be integer at 0 to 23'
            )

    @async_field_validator('minute')
    async def minute_validate(self, value):
        if not 0 <= value <= 59:
            raise HTTPException(
                400,
                detail=f'Minute must be integer at 0 to 59'
            )

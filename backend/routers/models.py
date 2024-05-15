import re
from typing import Optional

from fastapi import HTTPException
from pydantic import BaseModel
from pydantic_async_validation.validators import async_field_validator

from backend.utils import config

MAX_PASSWORD_LENGTH = config.getint('limitations', "MAX_PASSWORD_LENGTH")
MAX_EMAIL_LENGTH = config.getint('limitations', "MAX_EMAIL_LENGTH")
MAX_NAME_LENGTH = config.getint("limitations", "MAX_NAME_LENGTH")
MAX_DESCRIPTION_LENGTH = config.getint('limitations', "MAX_DESCRIPTION_LENGTH")
MIN_BORDER_RANGE = config.getint('limitations', "MIN_BORDER_RANGE")
MAX_BORDER_RANGE = config.getint('limitations', "MAX_BORDER_RANGE")


class UserIdApiModel(BaseModel):
    user_id: int


class PasswordApiModel(BaseModel):
    password: str
    @async_field_validator('password', mode='after')
    @classmethod
    async def password_validate(cls, password):
        if len(password) > MAX_PASSWORD_LENGTH:
            raise HTTPException(
                400,
                detail=f'Maximum password length is {MAX_PASSWORD_LENGTH}'
            )
        return password


class EmailApiModel(BaseModel):
    email: str
    @async_field_validator('email', mode='after')
    @classmethod
    async def email_validate(cls, email):
        if len(email) > MAX_EMAIL_LENGTH:
            raise HTTPException(
                400,
                detail=f'Maximum email length is {MAX_EMAIL_LENGTH}'
            )
        if not re.fullmatch(r'[a-zA-Z0-9]+@[a-zA-Z]+\.[a-zA-Z]', email):
            raise HTTPException(
                400,
                detail=f'Invalid email format'
            )
        return email


class AuthApiModel(BaseModel):
    user_id: UserIdApiModel
    password: Optional[PasswordApiModel] = None


class UpdatePasswordApiModel(BaseModel):
    user_id: UserIdApiModel
    hash: str


class TargetNameApiModel:
    name: str
    @async_field_validator("name", mode="before")
    @classmethod
    async def name_validate(cls, name):
        if len(name) > MAX_NAME_LENGTH:
            raise HTTPException(
                400,
                f"Max name length is {MAX_NAME_LENGTH}"
            )
        return name


class TargetDescriptionApiModel:
    description: str

    @async_field_validator("name", mode="before")
    @classmethod
    async def name_validate(cls, name):
        if len(name) > MAX_NAME_LENGTH:
            raise HTTPException(
                400,
                f"Max name length is {MAX_NAME_LENGTH}"
            )
        return name


class TargetApiModel(BaseModel):
    name: TargetNameApiModel
    border_progress: int | None = None
    description: TargetDescriptionApiModel | None = None


    @async_field_validator('border_progress', mode='before')
    @classmethod
    async def border_validate(cls, border_progress):
        if border_progress is not None:
            if not MIN_BORDER_RANGE <= border_progress <= MAX_BORDER_RANGE:
                raise HTTPException(
                    400,
                    detail=f'Days for completed target must be in range {MIN_BORDER_RANGE} to {MAX_BORDER_RANGE}'
                )
        return border_progress


class UpdateTargetApiModel(BaseModel):
    name: TargetNameApiModel | None = None
    description: TargetDescriptionApiModel | None = None


class NotificationTimeApiModel(BaseModel):
    hour: int
    minute: int

    @async_field_validator('hour', mode="before")
    @classmethod
    async def hour_validate(cls, hour):
        if not 0 <= hour <= 23:
            raise HTTPException(
                400,
                detail=f'Hour must be integer at 0 to 23'
            )
        return hour

    @async_field_validator('minute', mode="before")
    @classmethod
    async def minute_validate(cls, minute):
        if not 0 <= minute <= 59:
            raise HTTPException(
                400,
                detail=f'Minute must be integer at 0 to 59'
            )
        return minute




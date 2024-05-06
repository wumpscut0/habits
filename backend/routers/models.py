from typing import Optional

from fastapi import HTTPException
from pydantic import BaseModel, field_validator

from backend import config

MAX_PASSWORD_LENGTH = config.get('limitations', "MAX_PASSWORD_LENGTH")
MAX_EMAIL_LENGTH = config.get('limitations', "MAX_EMAIL_LENGTH")
MAX_DESCRIPTION_LENGTH = config.get('limitations', "MAX_DESCRIPTION_LENGTH")
MIN_BORDER_RANGE = config.get('limitations', "MIN_BORDER_RANGE")
MAX_BORDER_RANGE = config.get('limitations', "MAX_BORDER_RANGE")


class TelegramIdApiModel(BaseModel):
    telegram_id: int


class AuthApiModel(BaseModel):
    telegram_id: int
    password: Optional[str] = None

    @field_validator('password', mode='before')
    @classmethod
    def password_validate(cls, password):
        if len(password) > MAX_PASSWORD_LENGTH:
            raise HTTPException(
                400,
                detail=f'Maximum password length is {MAX_PASSWORD_LENGTH}'
            )
        return password


class UpdatePasswordApiModel(BaseModel):
    hash_: str
    email: str | None = None

    @field_validator('email', mode='before')
    @classmethod
    def email_validate(cls, email):
        if len(email) > MAX_EMAIL_LENGTH:
            raise HTTPException(
                400,
                detail=f'Maximum email length is {MAX_EMAIL_LENGTH}'
            )
        return email


class TargetApiModel(BaseModel):
    name: str
    description: str | None = None
    border_progress: int | None = None

    @field_validator('border_progress', mode='before')
    @classmethod
    def border_progress_validate(cls, border):
        if not MIN_BORDER_RANGE <= border <= MAX_BORDER_RANGE:
            raise HTTPException(
                400,
                detail=f'Days for completed target must be in range {MIN_BORDER_RANGE} to {MAX_BORDER_RANGE}'
            )
        return border

    @field_validator('description', mode='before')
    @classmethod
    def description_validate(cls, description):
        if len(description) > MAX_DESCRIPTION_LENGTH:
            raise HTTPException(
                400,
                detail=f'Max description length is {MAX_DESCRIPTION_LENGTH} symbols'
            )
        return description


class NotificationTimeApiModel(BaseModel):
    hour: int
    minute: int

    @field_validator('hour', mode="before")
    @classmethod
    def hour_validate(cls, hour):
        if not 0 <= hour <= 23:
            raise HTTPException(
                400,
                detail=f'Hour must be integer at 0 to 23'
            )
        return hour

    @field_validator('minute', mode="before")
    @classmethod
    def minute_validate(cls, minute):
        if not 0 <= minute <= 59:
            raise HTTPException(
                400,
                detail=f'Minute must be integer at 0 to 59'
            )
        return minute




from typing import Optional

from fastapi import HTTPException
from pydantic import BaseModel, model_validator, field_validator

from backend.config import MIN_BORDER_RANGE, MAX_BORDER_RANGE, MAX_DESCRIPTION_LENGTH


class TelegramId(BaseModel):
    telegram_id: int


class Auth(BaseModel):
    telegram_id: int
    password: Optional[str] = None


class UpdatePassword(BaseModel):
    hash: str
    email: str | None = None


class HabitM(BaseModel):
    name: str
    description: str | None = None
    border_progress: int | None = None

    @field_validator('border_progress', mode='before')
    @classmethod
    def border_progress(cls, border):
        if not MIN_BORDER_RANGE <= border <= MAX_BORDER_RANGE:
            raise HTTPException(
                400,
                detail=f'Days for completed target must be in range {MIN_BORDER_RANGE} to {MAX_BORDER_RANGE}'
            )
        return border

    @field_validator('description', mode='before')
    @classmethod
    def border_progress(cls, description):
        if len(description) > MAX_DESCRIPTION_LENGTH:
            raise HTTPException(
                400,
                detail=f'Max description length is {MAX_DESCRIPTION_LENGTH} symbols'
            )
        return description



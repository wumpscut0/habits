from typing import Optional

from fastapi import HTTPException
from pydantic import BaseModel, model_validator

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
    user_id: int
    name: str
    description: str | None = None
    border_progress: int | None = None

    @model_validator(mode='after')
    def border_progress(self):
        if not MIN_BORDER_RANGE <= self.border_progress <= MAX_BORDER_RANGE:
            raise HTTPException(
                400,
                detail=f'Days for completed target must be in range {MIN_BORDER_RANGE} to {MAX_BORDER_RANGE}'
            )
        if len(self.description) > MAX_DESCRIPTION_LENGTH:
            raise HTTPException(
                400,
                detail=f'Max description length is {MAX_DESCRIPTION_LENGTH} symbols'
            )
        return self

from typing import Optional

from pydantic import BaseModel


class SignUp(BaseModel):
    telegram_id: int


class Auth(BaseModel):
    telegram_id: int
    password: Optional[str] = None


class UpdatePassword(BaseModel):
    telegram_id: int
    hash: str

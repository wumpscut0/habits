from pydantic import BaseModel


class SignUp(BaseModel):
    telegram_id: int


class Auth(BaseModel):
    telegram_id: int
    password: str | None


class AuthWithPassword(BaseModel):
    telegram_id: int
    hash: str

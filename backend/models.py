from pydantic import BaseModel


class JWT(BaseModel):
    jwt: str


class SignUp(BaseModel):
    telegram_id: int
    nickname: str
    login: str
    password: str


class SignIn(BaseModel):
    login: str
    password: str

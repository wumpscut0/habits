from pydantic import BaseModel


class JWT(BaseModel):
    jwt: str


class SignIn(BaseModel):
    id: int
    nickname: str
    login: str
    hash: str

import os
import jwt
from backend.database import Session
from backend.routers.models import Auth, SignUp, UpdatePassword
from backend.database.queries import authorization, update_password, sign_up, get_user
from fastapi import FastAPI, Header, HTTPException
from typing import Annotated

from backend.routers.utils import verify_password

app = FastAPI()


@app.post("/sign_up")
async def sign_up_(sign_up__: SignUp):
    async with Session.begin() as session:
        await sign_up(session, **sign_up__.model_dump())


@app.patch('/update_password')
async def update_password_(update_password__: UpdatePassword, Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        await authorization(session, Authorization)
        await update_password(session, **update_password__.model_dump())


@app.post("/sign_in")
async def sign_in(auth: Auth):
    async with Session.begin() as session:
        user = await get_user(session, auth.telegram_id)
        if user.hash is not None and auth.hash is None:
            raise HTTPException(400, 'Give me hash')
        elif user.hash is not None and auth.password:
            await verify_password(auth.password, user.hash)

        return jwt.encode(auth.model_dump(), os.getenv('JWT'))

import os
import jwt
import asyncio
import pydantic
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from backend.database import Session
from backend.models import SignUp, JWT, SignIn
from backend.database.queries import sign_up_,  sign_in_, is_exist_login
from fastapi import FastAPI
app = FastAPI()


@app.post('/sign_up', status_code=201)
async def sign_up(x: JWT):
    try:
        data = jwt.decode(x.jwt, key=os.getenv('JWT'), algorithms="HS256")
        data = SignUp.model_validate(data)
        async with Session.begin() as session:
            await sign_up_(session, data)
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=400, detail="Invalid jwt token"
        )
    except pydantic.ValidationError:
        raise HTTPException(
            status_code=422, detail="Validation error"
        )
    except IntegrityError:
        raise HTTPException(
            status_code=409, detail=f"User with login {data.login} already exist"
        )


@app.post("/sign_in")
async def sign_in(x: JWT):
    try:
        data = jwt.decode(x.jwt, key=os.getenv('JWT'), algorithms='HS256')
        data = SignIn.model_validate(data)
        async with Session.begin() as session:
            user = await sign_in_(session, data)
            if user:
                return {
                    "success": True,
                    "nickname": user.nickname
                }
            raise HTTPException(
                status_code=401, detail=f"Wrong login or password"
            )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=400, detail="Invalid jwt token"
        )
    except pydantic.ValidationError:
        raise HTTPException(
            status_code=422, detail="Validation error"
        )


@app.get('/verify_login/{login}', status_code=200)
async def verify_login(login: str):
    async with Session.begin() as session:
        if not await is_exist_login(session, login):
            return {"success": True}

    raise HTTPException(
        409, f'User with login "{login}" already exists.'
    )

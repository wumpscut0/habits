import os
import jwt
import asyncio
import pydantic
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from backend.database import Session
from backend.models import SignUp, JWT
from backend.database.queries import sign_in__, verify_login_
from fastapi import FastAPI
app = FastAPI()


@app.post('/sign_up/{sign_up}', status_code=201)
async def sign_in_(sign_up: str):
    try:
        payload = jwt.decode(sign_up, key=os.getenv('JWT'), algorithms="HS256")
        print(payload)
        data = SignUp.model_validate(payload)
        async with Session.begin() as session:
            await sign_in__(session, data)
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=400, detail="Invalid jwt token"
        )
    except pydantic.ValidationError:
        raise HTTPException(
            status_code=400, detail="Validation error"
        )
    except IntegrityError:
        raise HTTPException(
            status_code=409, detail=f"User with {data.login} already exist"
        )


@app.get('/verify_login/{login}', status_code=200)
async def verify_login(login: str):
    async with Session.begin() as session:
        if not await verify_login_(session, login):
            return {"success": True}
    raise HTTPException(status_code=409, detail="Login already using")


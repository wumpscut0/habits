from contextlib import asynccontextmanager

from fastapi import Request, FastAPI, HTTPException, Depends

from server.api.authority import Authority
from server.api.models import AuthApiModel, Token
from server.api.targets import targets_router
from server.api.users import users_router
from server.database import create_all

from server.utils.loggers import errors


app = FastAPI(dependencies=[Depends(Authority.authenticate_service)])
app.include_router(users_router)
app.include_router(targets_router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_all()
    yield


@app.middleware('http')
async def error_abyss(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        errors.critical(f"{call_next.__name__}\n{e}")
        print(e)

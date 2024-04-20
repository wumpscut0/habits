from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import User
from backend.models import SignUp, SignIn
from passlib.hash import pbkdf2_sha256


async def sign_up_(session: AsyncSession, data: SignUp):
    await session.execute(insert(User).values(**data.model_dump()))
    await session.commit()


async def sign_in_(session: AsyncSession, data: SignIn):
    user = await session.get(User, ident=data.login)
    if user is None or not pbkdf2_sha256.verify(data.password, user.password):
        return False
    return user


async def is_exist_login(session: AsyncSession, login: str):
    return not (await session.execute(select(User).where(User.login == login))).one_or_none() is None






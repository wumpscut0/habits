from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import User
from backend.models import SignIn


async def sign_in__(session: AsyncSession, data: SignIn):
    await session.execute(insert(User).values(**data.model_fields))
    await session.commit()


async def verify_login_(session: AsyncSession, login: str):
    return (await session.execute(select(User).where(User.login == login))).one_or_none()




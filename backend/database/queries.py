from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import User
from backend.models import SignUp


async def sign_in__(session: AsyncSession, data: SignUp):
    await session.execute(insert(User).values(**data.model_dump()))
    await session.commit()


async def verify_login_(session: AsyncSession, login: str):
    return (await session.execute(select(User).where(User.login == login))).one_or_none()




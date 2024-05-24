import os
from configparser import ConfigParser

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from dotenv import load_dotenv, find_dotenv

from server.database.models import Base

load_dotenv(find_dotenv())

config = ConfigParser()

config.read(os.path.abspath(os.path.join(os.path.dirname(__file__), "alembic.ini")))

engine = create_async_engine(os.getenv("DATABASE") + "/habits")
Session = async_sessionmaker(engine, expire_on_commit=False)


async def create_all():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_all():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

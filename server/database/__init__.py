import os
import configparser

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from dotenv import load_dotenv, find_dotenv

from server.database.models import Base

load_dotenv(find_dotenv())

# config = configparser.ConfigParser()
# config.read('/server/database/alembic.ini')
# config.set('alembic', 'sqlalchemy.url', os.getenv("DATABASE") + '/habits')
#
# with open('/server/database/alembic.ini', 'w') as configfile:
#     config.write(configfile)


engine = create_async_engine(os.getenv('DATABASE') + '/habits')
Session = async_sessionmaker(engine, expire_on_commit=False)


async def create_all():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata)

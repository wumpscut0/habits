import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

engine = create_async_engine(os.getenv('DATABASE'))
Session = async_sessionmaker(engine)


# async def create_all():
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata)
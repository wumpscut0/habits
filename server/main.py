import os

import uvicorn
import asyncio
import subprocess

from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError

from server.database import create_all, Session
from server.database.models import ServiceORM


async def startup():
    await create_all()
    async with Session.begin() as session:
        try:
            await session.execute(
                insert(ServiceORM).values(
                    {"id": "Psychological", "api_key": os.getenv("API_KEY")}
                )
            )
        except IntegrityError:
            pass


if __name__ == "__main__":
    asyncio.run(startup())
    uvicorn.run(
        "api:app",
        host=os.getenv("UVICORN_IP"),
        port=int(os.getenv("UVICORN_PORT")),
        reload=True,
    )

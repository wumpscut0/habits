from typing import Annotated

from fastapi import Header, Query

from backend.database import Session
from backend.routers.models import TargetApiModel, UpdateTargetApiModel
from backend.database.queries import TargetsQueries
from backend.utils import config
from backend.routers import app, Authority

MAX_NAME_LENGTH = config.getint('limitations', 'MAX_NAME_LENGTH')
MAX_DESCRIPTION_LENGTH = config.getint('limitations', 'MAX_DESCRIPTION_LENGTH')


@app.get('/targets')
async def get_targets(Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        user = await Authority.user_authentication(Authorization)
        return await TargetsQueries.get_targets(session, user.user_id)


@app.get("/target/{target_id}")
async def get_target(target_id: int, Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        await Authority.user_authentication(Authorization)

        await TargetsQueries.get_target(session, target_id)
        return await TargetsQueries.get_target(session, target_id)


@app.post('/targets', status_code=201)
async def create_target(target_api_model: TargetApiModel, Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        user = await Authority.user_authentication(Authorization)
        await TargetsQueries.create(session, user.user_id, **target_api_model.model_dump())


@app.put('/targets/{target_id}')
async def update_target_name(
        target_id: int,
        update_target_api_model: UpdateTargetApiModel,
        Authorization: Annotated[str, Header()],
):
    async with Session.begin() as session:
        await Authority.user_authentication(Authorization)

        await TargetsQueries.get_target(session, target_id)
        await TargetsQueries.update(session, **update_target_api_model.model_dump())


@app.delete('/targets/{target_id}')
async def delete_target(target_id: int, Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        await Authority.user_authentication(Authorization)

        await TargetsQueries.get_target(session, target_id)
        await TargetsQueries.delete(session, target_id)


@app.patch('/targets/{target_id}/invert')
async def invert_target_completed(target_id: int, Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        await Authority.user_authentication(Authorization)

        await TargetsQueries.get_target(session, target_id)
        return await TargetsQueries.invert_completed(session, target_id)


@app.patch('/targets/progress')
async def increase_targets_progress(Authorization: Annotated[str, Header()]):
    async with Session.begin() as session:
        await Authority.service_authentication(Authorization)

        await TargetsQueries.increase_progress(session)

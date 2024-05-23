from typing import Annotated

from fastapi import Depends, APIRouter

from server.database import Session
from server.api.models import TargetApiModel, UpdateTargetApiModel, Payload
from server.database.queries import TargetsQueries
from server.utils import config
from server.api import Authority

MAX_NAME_LENGTH = config.getint('limitations', 'MAX_NAME_LENGTH')
MAX_DESCRIPTION_LENGTH = config.getint('limitations', 'MAX_DESCRIPTION_LENGTH')

targets_router = APIRouter(prefix="/targets")


@targets_router.get('/')
async def get_targets(payload: Annotated[Payload, Depends(Authority.user_authorization)]):
    async with Session.begin() as session:
        return await TargetsQueries.get_targets(session, payload["sub"])


@targets_router.get("/{target_id}", dependencies=[Depends(Authority.user_authorization)])
async def get_target(target_id: int):
    async with Session.begin() as session:
        return await TargetsQueries.get_target(session, target_id)


@targets_router.post('/', status_code=201)
async def create_target(
        target_api_model: TargetApiModel,
        payload: Annotated[Payload, Depends(Authority.user_authorization)]
):
    async with Session.begin() as session:
        await TargetsQueries.create(session, payload["sub"], **target_api_model.model_dump())


@targets_router.put('/{target_id}', dependencies=[Depends(Authority.user_authorization)])
async def update_target_name(
        target_id: int,
        update_target_api_model: UpdateTargetApiModel,
):
    async with Session.begin() as session:
        await TargetsQueries.get_target(session, target_id)
        await TargetsQueries.update(session, target_id, **update_target_api_model.model_dump())


@targets_router.delete('/{target_id}', dependencies=[Depends(Authority.user_authorization)])
async def delete_target(target_id: int):
    async with Session.begin() as session:
        await TargetsQueries.get_target(session, target_id)
        await TargetsQueries.delete(session, target_id)


@targets_router.patch('/{target_id}/invert', dependencies=[Depends(Authority.user_authorization)])
async def invert_target_completed(target_id: int):
    async with Session.begin() as session:
        await TargetsQueries.get_target(session, target_id)
        return await TargetsQueries.invert_completed(session, target_id)


@targets_router.patch('/progress')
async def increase_targets_progress():
    async with Session.begin() as session:
        await TargetsQueries.increase_progress(session)

from datetime import datetime

from sqlalchemy import update, insert, select, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from server.api.models import UserApiModel, UpdatePasswordApiModel
from server.database.models import UserORM, TargetORM, ServiceORM


class ServiceQueries:
    @staticmethod
    async def get_service(session: AsyncSession, service_id: str):
        return await session.get(ServiceORM, service_id)


class UserQueries:
    @staticmethod
    async def registration(session: AsyncSession, user_api_model: UserApiModel):
        try:
            await session.execute(insert(UserORM).values({
                "id": user_api_model.user_id,
                "hash": user_api_model.hash,
                "email": user_api_model.email,
            }))
        except IntegrityError:
            raise HTTPException(409, "User already exists")

    @staticmethod
    async def get_users(session: AsyncSession):
        return [
            user.as_dict_()
            for user in (await session.execute(select(UserORM))).scalars()
        ]

    @staticmethod
    async def get_user(session: AsyncSession, user_id: str):
        user = await session.get(UserORM, ident=user_id)
        if user is None:
            raise HTTPException(404)
        return user.as_dict_()


class PasswordQueries:
    @staticmethod
    async def update_password(session: AsyncSession, update_password_api_model: UpdatePasswordApiModel):
        await session.execute(update(UserORM)
                              .where(UserORM.id == update_password_api_model.user_id)
                              .values({"hash": update_password_api_model.hash}))

    @staticmethod
    async def delete_password(session: AsyncSession, user_id: str):
        await session.execute(update(UserORM).where(UserORM.id == user_id).values({"hash": None}))


class EmailQueries:
    @staticmethod
    async def update(session: AsyncSession, user_id: str, email: str):
        await session.execute(update(UserORM).where(UserORM.id == user_id).values({"email": email}))

    @staticmethod
    async def delete(session: AsyncSession, user_id: str):
        await session.execute(update(UserORM).where(UserORM.id == user_id).values({"email": None}))


class NotificationsQueries:
    @staticmethod
    async def on(session: AsyncSession, user_id: str):
        return (await session.execute(select(UserORM.notifications).where(UserORM.id == user_id))).scalar()

    @staticmethod
    async def update(session: AsyncSession, user_id: str, time):
        await session.execute(update(UserORM).values({"notification_time": time}).where(
            UserORM.id == user_id))

    @staticmethod
    async def invert(session: AsyncSession, user_id: str):
        notifications = (await session.execute(select(UserORM.notifications).where(UserORM.id == user_id))).scalar()
        await session.execute(update(UserORM).where(UserORM.id == user_id).values({"notifications": not notifications}))
        return 0 if notifications else 1


class TargetsQueries:
    @staticmethod
    async def create(
            session: AsyncSession,
            user_id: str,
            name: str,
            description: str | None = None,
            border_progress: int | None = None
    ):
        await session.execute(insert(TargetORM).values(
            user_id=user_id, name=name, description=description, border_progress=border_progress))

    @staticmethod
    async def delete(session: AsyncSession, target_id: int):
        await session.execute(delete(TargetORM).where(TargetORM.id == target_id))

    @staticmethod
    async def get_targets(session: AsyncSession, user_id: str):
        return [
            target.as_dict_()
            for target in (await session.execute(
                select(TargetORM)
                .filter(TargetORM.user_id == user_id)
            )).scalars()
        ]

    @staticmethod
    async def get_target(session: AsyncSession, target_id: int):
        target = await session.get(TargetORM, ident=target_id)
        if target is None:
            raise HTTPException(404)
        return target.as_dict_()

    @staticmethod
    async def update(session: AsyncSession, target_id: int, **kwargs):
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        await session.execute(
            update(TargetORM)
            .values(kwargs)
            .filter(TargetORM.id == target_id)
        )

    @staticmethod
    async def invert_completed(session: AsyncSession, target_id: int):
        completed = (await session.execute(
            select(TargetORM.completed)
            .filter(TargetORM.id == target_id)
        )).scalar()

        await session.execute(
            update(TargetORM)
            .values({'completed': not completed})
            .filter(TargetORM.id == target_id)
        )
        return 1 if completed else 0

    @staticmethod
    async def increase_progress(session: AsyncSession):
        await session.execute(update(TargetORM).values({"progress": TargetORM.progress + 1}).filter(
            TargetORM.progress + 1 <= TargetORM.border_progress, TargetORM.completed
        ))
        await session.execute(update(TargetORM).values({"completed": False}).filter(
            TargetORM.progress != TargetORM.border_progress
        ))
        await session.execute(update(TargetORM).values({"completed_datetime": datetime.now()}).filter(
            TargetORM.progress == TargetORM.border_progress, TargetORM.completed_datetime is None
        ))

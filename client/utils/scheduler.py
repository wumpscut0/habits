import os

from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.triggers.cron import CronTrigger

from client.api import Api
from client.bot import BotControl
from client.markups import Info
from client.utils import config, Emoji

from client.utils.loggers import info, errors
from client.utils.redis import Storage, CustomRedis

MINUTE_INCREASE_PROGRESS = config.getint("limitations", "MINUTE_INCREASE_PROGRESS")
HOUR_INCREASE_PROGRESS = config.getint("limitations", "HOUR_INCREASE_PROGRESS")


class Scheduler:
    _jobstores = {"default": RedisJobStore(db=2, host=os.getenv("REDIS_HOST"))}
    _job_defaults = {"coalesce": False, "max_instances": 1}
    scheduler = AsyncIOScheduler()
    scheduler.configure(jobstores=_jobstores, job_defaults=_job_defaults)

    _increase_progress_id = "increase_progress"
    _api = Api

    @classmethod
    def set_job_increase_progress(
        cls, hour=HOUR_INCREASE_PROGRESS, minute=MINUTE_INCREASE_PROGRESS
    ):
        cls.scheduler.add_job(
            Workers.increase_progress,
            "cron",
            id=cls._increase_progress_id,
            replace_existing=True,
            hour=hour,
            minute=minute,
        )

    @classmethod
    async def refresh_notifications(cls, user_id: str):
        """
        Notifications will be on in case:
        1) User have any not marked target
        2) User have on notifications
        """
        user, user_code = await cls._api.get_user(user_id)
        targets, targets_code = await cls._api.get_targets(Storage(user_id).user_token)
        if user_code == 200 and targets_code == 200:
            all_done = True
            for target in targets:
                if not target["completed"]:
                    all_done = False
                    break
            if user["notifications"] and not all_done:
                time_ = user["notification_time"]
                cls.scheduler.add_job(
                    func=Workers.remainder,
                    trigger=CronTrigger(hour=time_["hour"], minute=time_["minute"]),
                    args=(int(user_id),),
                    replace_existing=True,
                    id=user_id,
                )
                info.info(f"Notifications on for user {user_id}")
            else:
                try:
                    cls.scheduler.remove_job(job_id=user_id, jobstore="default")
                    info.info(f"Notifications off for user {user_id}")
                except JobLookupError:
                    pass
        else:
            errors.critical(f"Failed refresh notification for user: {user_id}")


class Workers:
    _api = Api

    @staticmethod
    async def remainder(user_id: int):
        await BotControl(user_id).create_text_message(
            Info(f"Don`t forget mark done targets today {Emoji.SPROUT}")
        )
        info.info(f"Remaining sent to user {user_id}")

    @classmethod
    async def increase_progress(cls):
        _, code = await cls._api.increase_progress()

        if code == 200:
            info.info(f"Progress increased")
            users, code = await cls._api.get_users()
            if code == 200:
                for user in users:
                    await Scheduler.refresh_notifications(user["id"])
                info.info("Refreshed notifications for all users")
            errors.critical("Refreshed notifications for all users failed")
        else:
            errors.critical(f"Progress not increased. Status: {code}")
            storage = CustomRedis(
                host=os.getenv("REDIS_HOST"), port=int(os.getenv("REDIS_PORT")), db=1
            )
            count = storage.get(f"not_increase_count")
            if count is None:
                count = 0
            count += 1
            storage.set(f"not_increase_count", count)

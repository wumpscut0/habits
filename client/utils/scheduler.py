from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.triggers.cron import CronTrigger

from client.api import Api
from client.bot import BotControl
from client.markups import Info

from client.utils.loggers import info, errors
from client.utils.redis import HourGlassAnimationIdsPull


class Scheduler:
    _jobstores = {
        'default': RedisJobStore(db=2)
    }
    _job_defaults = {
        'coalesce': False,
        'max_instances': 1
    }
    scheduler = AsyncIOScheduler()
    scheduler.configure(jobstores=_jobstores, job_defaults=_job_defaults)

    _increase_progress_id = "increase_progress"
    _api = Api()
    _hour_glass_animation_ids_pull = HourGlassAnimationIdsPull()

    @classmethod
    def set_job_increase_progress(cls, hour=0, minute=0):
        cls.scheduler.add_job(
            Workers.increase_progress,
            'cron',
            id=cls._increase_progress_id,
            replace_existing=True,
            hour=hour,
            minute=minute,
        )

    @classmethod
    async def refresh_notifications(cls, user_id: str):
        user_response = await cls._api.get_user(user_id)
        targets_response = await cls._api.get_targets(user_id)
        if user_response.status == 200 and targets_response.status == 200:
            user = (await user_response.json())
            targets = (await targets_response.json())
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
                    args=(int(user_id),), replace_existing=True, id=user_id
                )
            else:
                try:
                    cls.scheduler.remove_job(job_id=user_id, jobstore="default")
                except JobLookupError:
                    pass


class Workers:
    @staticmethod
    async def remainder(user_id: int):
        await BotControl(user_id).create_text_message(Info('Don`t forget mark done target today').text_message_markup, context=False)
        info.info(f'Remaining sent to user {user_id}')

    @staticmethod
    async def increase_progress():
        api = Api()
        response = await api.increase_progress()
        if response.status == 200:
            info.info(f'Progress increased')
        else:
            errors.error(f"Progress not increased. Status: {response.status}")

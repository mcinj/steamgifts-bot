import os

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.blocking import BlockingScheduler

from .log import get_logger

logger = get_logger(__name__)


class Scheduler:
    class __Scheduler:
        def __init__(self):
            jobstores = {
                'default': SQLAlchemyJobStore(url=f"{os.getenv('BOT_DB_URL', 'sqlite:///./config/sqlite.db')}")
            }
            job_defaults = {
                'coalesce': True,
                'max_instances': 3
            }
            self.scheduler = BlockingScheduler(jobstores=jobstores, job_defaults=job_defaults)

        def __getattr__(self, name):
            return getattr(self.scheduler, name)

    instance = None

    def __init__(self):
        if not Scheduler.instance:
            Scheduler.instance = Scheduler.__Scheduler()

    def __getattr__(self, name):
        return getattr(self.instance, name)

import datetime
import threading
from datetime import timedelta, datetime
from threading import Thread
from time import sleep

from .enter_giveaways import EnterGiveaways
from .evaluate_won_giveaways import EvaluateWonGiveaways
from .log import get_logger
from .scheduler import Scheduler

logger = get_logger(__name__)


class GiveawayThread(threading.Thread):

    def __init__(self, config, notification):
        Thread.__init__(self)
        self.exc = None
        self.config = config
        self.notification = notification
        logger.debug("Creating scheduler")
        self._scheduler = Scheduler()
        self.won_giveaway_job_id = 'eval_won_giveaways'
        self.evaluate_giveaway_job_id = 'eval_giveaways'

        if config['DEFAULT'].getboolean('enabled'):
            cookie = config['DEFAULT'].get('cookie')
            user_agent = config['DEFAULT'].get('user_agent')

            minimum_points = config['DEFAULT'].getint('minimum_points')
            max_entries = config['DEFAULT'].getint('max_entries')
            max_time_left = config['DEFAULT'].getint('max_time_left')
            minimum_game_points = config['DEFAULT'].getint('minimum_game_points')
            blacklist = config['DEFAULT'].get('blacklist_keywords')

            self._all_page = EnterGiveaways(cookie, user_agent, 'All', False, minimum_points, max_entries,
                                            max_time_left, minimum_game_points, blacklist, notification)

        if config['WISHLIST'].getboolean('wishlist.enabled'):
            wishlist_minimum_points = config['WISHLIST'].getint('wishlist.minimum_points')
            wishlist_max_entries = config['WISHLIST'].getint('wishlist.max_entries')
            wishlist_max_time_left = config['WISHLIST'].getint('wishlist.max_time_left')

            self._wishlist_page = EnterGiveaways(cookie, user_agent, 'Wishlist', False, wishlist_minimum_points,
                                                 wishlist_max_entries, wishlist_max_time_left, 0, '', notification)

        if not self._all_page and not self._wishlist_page:
            logger.error("⁉️ Both 'Default' and 'Wishlist' configurations are disabled. Nothing will run. Exiting...")
            sleep(10)
            exit(-1)

        self._won_page_job_function = EvaluateWonGiveaways(cookie, user_agent, notification).start
        won_giveaway_job = self._scheduler.get_job(job_id=self.won_giveaway_job_id)
        if won_giveaway_job:
            logger.debug("Previous won giveaway evaluator job exists. Removing.")
            won_giveaway_job.remove()
        self._scheduler.add_job(self._won_page_job_function,
                                id=self.won_giveaway_job_id,
                                trigger='interval',
                                max_instances=1,
                                replace_existing=True,
                                hours=12,
                                next_run_time=datetime.now() + timedelta(minutes=5),
                                jitter=8000)

        evaluate_giveaway_job = self._scheduler.get_job(job_id=self.evaluate_giveaway_job_id)
        if evaluate_giveaway_job:
            logger.debug("Previous giveaway evaluator job exists. Removing.")
            evaluate_giveaway_job.remove()
        runner = GiveawayThread.GiveawayRunner(self._wishlist_page, self._all_page,
                                               self.evaluate_giveaway_job_id)
        self._scheduler.add_job(runner.run,
                                id=self.evaluate_giveaway_job_id,
                                trigger='interval',
                                max_instances=1,
                                replace_existing=True,
                                minutes=44,
                                next_run_time=datetime.now(),
                                jitter=900)

    def run(self):
        # Variable that stores the exception, if raised by someFunction
        self.exc = None
        try:
            self._scheduler.start()
        except BaseException as e:
            self.exc = e

    def join(self):
        threading.Thread.join(self)
        # Since join() returns in caller thread
        # we re-raise the caught exception
        # if any was caught
        if self.exc:
            raise self.exc

    class GiveawayRunner:

        def __init__(self, wishlist_page, all_page, job_id):
            self._wishlist_page = wishlist_page
            self._all_page = all_page
            self._job_id = job_id

        def run(self):
            logger.info("🟢 Evaluating giveaways.")
            if self._wishlist_page:
                self._wishlist_page.start()
            if self._all_page:
                self._all_page.start()
            logger.info("🔴 All giveaways evaluated.")
            scheduler = Scheduler()
            evaluate_giveaway_job = scheduler.get_job(job_id=self._job_id)
            if evaluate_giveaway_job:
                when_to_start_again = evaluate_giveaway_job.next_run_time
                logger.info(f"🛋 Going to sleep. Will start again at {when_to_start_again}")
            else:
                logger.info("No set time to evaluate giveaways again.")
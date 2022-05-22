import os
from datetime import datetime, timedelta

import sqlalchemy
from alembic import command
from alembic.config import Config
from dateutil import tz
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from sqlalchemy_utils import database_exists

from .log import get_logger
from .models import TableNotification, TableGiveaway, TableSteamItem

logger = get_logger(__name__)
engine = sqlalchemy.create_engine(f"{os.getenv('BOT_DB_URL', 'sqlite:///./config/sqlite.db')}", echo=False)
engine.connect()


def run_db_migrations(script_location: str, db_url: str) -> None:
    logger.debug('Running DB migrations in %r on %r', script_location, db_url)
    alembic_cfg = Config()
    alembic_cfg.set_main_option('script_location', script_location)
    alembic_cfg.set_main_option('sqlalchemy.url', db_url)

    if not database_exists(db_url):
        logger.debug(f"'{db_url}' does not exist. Running normal migration to create db and tables." )
        command.upgrade(alembic_cfg, 'head')
    elif database_exists(db_url):
        logger.debug(f"'{db_url}' exists.")
        insp = sqlalchemy.inspect(engine)
        alembic_version_table_name = 'alembic_version'
        has_alembic_table = insp.has_table(alembic_version_table_name)
        if has_alembic_table:
            logger.debug(f"Table '{alembic_version_table_name}' exists.")
        else:
            logger.debug(f"Table '{alembic_version_table_name}' doesn't exist so assuming it was created pre-alembic "
                         f"setup. Setting the version to the first version created prior to alembic setup.")
            alembic_first_ref = '1da33402b659'
            command.stamp(alembic_cfg, alembic_first_ref)
        logger.debug("Running migration.")
        command.upgrade(alembic_cfg, 'head')


class NotificationHelper:

    @classmethod
    def get(cls):
        with Session(engine) as session:
            return session.query(TableNotification).order_by(TableNotification.created_at.desc()).all()

    @classmethod
    def insert(cls, type_of_error, message, medium, success):
        with Session(engine) as session:
            n = TableNotification(type=type_of_error, message=message, medium=medium, success=success)
            session.add(n)
            session.commit()

    @classmethod
    def get_won_notifications_today(cls):
        with Session(engine) as session:
            # with how filtering of datetimes works with a sqlite backend I couldn't figure out a better way
            # to filter out the dates to local time when they are stored in utc in the db
            within_3_days = session.query(TableNotification) \
                .filter(func.DATE(TableNotification.created_at) >= (datetime.utcnow().date() - timedelta(days=1))) \
                .filter(func.DATE(TableNotification.created_at) <= (datetime.utcnow().date() + timedelta(days=1))) \
                .filter_by(type='won').all()
            actual = []
            for r in within_3_days:
                if r.created_at.replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal()).date() == datetime.now(
                        tz=tz.tzlocal()).date():
                    actual.append(r)
            return actual

    @classmethod
    def get_won_notifications(cls):
        with Session(engine) as session:
            return session.query(TableNotification) \
                .filter_by(type='won') \
                .all()

    @classmethod
    def get_error_notifications(cls):
        with Session(engine) as session:
            return session.query(TableNotification) \
                .filter_by(type='error') \
                .all()


class GiveawayHelper:

    @classmethod
    def get(cls):
        with Session(engine) as session:
            return session.query(TableGiveaway).options(joinedload('steam_item')).order_by(TableGiveaway.giveaway_ended_at.desc()).all()

    @classmethod
    def unix_timestamp_to_utc_datetime(cls, timestamp):
        return datetime.utcfromtimestamp(timestamp)

    @classmethod
    def get_by_ids(cls, giveaway):
        with Session(engine) as session:
            return session.query(TableGiveaway).filter_by(giveaway_id=giveaway.giveaway_game_id,
                                                          steam_id=giveaway.steam_app_id).all()

    @classmethod
    def insert(cls, giveaway, entered):
        with Session(engine) as session:
            result = session.query(TableSteamItem).filter_by(steam_id=giveaway.steam_app_id).all()
            if result:
                steam_id = result[0].steam_id
            else:
                item = TableSteamItem(
                    steam_id=giveaway.steam_app_id,
                    steam_url=giveaway.steam_url,
                    game_name=giveaway.game_name)
                session.add(item)
                session.flush()
                steam_id = item.steam_id
            g = TableGiveaway(
                giveaway_id=giveaway.giveaway_game_id,
                steam_id=steam_id,
                giveaway_uri=giveaway.giveaway_uri,
                user=giveaway.user,
                giveaway_created_at=GiveawayHelper.unix_timestamp_to_utc_datetime(giveaway.time_created_timestamp),
                giveaway_ended_at=GiveawayHelper.unix_timestamp_to_utc_datetime(giveaway.time_remaining_timestamp),
                cost=giveaway.cost,
                copies=giveaway.copies,
                contributor_level=giveaway.contributor_level,
                entered=entered,
                game_entries=giveaway.game_entries)
            session.add(g)
            session.commit()

    @classmethod
    def upsert_giveaway(cls, giveaway, entered):
        result = GiveawayHelper.get_by_ids(giveaway)
        if not result:
            GiveawayHelper.insert(giveaway, entered)
        else:
            with Session(engine) as session:
                g = TableGiveaway(
                    giveaway_id=giveaway.giveaway_game_id,
                    steam_id=result[0].steam_id,
                    giveaway_uri=giveaway.giveaway_uri,
                    user=giveaway.user,
                    giveaway_created_at=GiveawayHelper.unix_timestamp_to_utc_datetime(giveaway.time_created_timestamp),
                    giveaway_ended_at=GiveawayHelper.unix_timestamp_to_utc_datetime(giveaway.time_remaining_timestamp),
                    cost=giveaway.cost,
                    copies=giveaway.copies,
                    contributor_level=giveaway.contributor_level,
                    entered=entered,
                    game_entries=giveaway.game_entries)
                session.merge(g)
                session.commit()
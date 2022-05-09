from datetime import datetime

from sqlalchemy import create_engine, Integer, String, Column, DateTime, Boolean, func, ForeignKey
from sqlalchemy.orm import registry, relationship, Session
from sqlalchemy_utils import database_exists, create_database

mapper_registry = registry()
mapper_registry.metadata
Base = mapper_registry.generate_base()
engine = create_engine('sqlite:///../config/sqlite.db', echo=False)


class TableNotification(Base):
    __tablename__ = 'notification'
    id = Column(Integer, primary_key=True, nullable=False)
    type = Column(String(50), nullable=False)
    message = Column(String(300), nullable=False)
    medium = Column(String(50), nullable=False)
    success = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __mapper_args__ = {"eager_defaults": True}

    @classmethod
    def get_won_notifications_today(cls):
        with Session(engine) as session:
            return session.query(TableNotification)\
                .filter(func.DATE(TableNotification.created_at) == datetime.utcnow().date())\
                .filter_by(type='won')\
                .all()


class TableSteamItem(Base):
    __tablename__ = 'steam_item'
    steam_id = Column(String(15), primary_key=True, nullable=False)
    game_name = Column(String(200), nullable=False)
    steam_url = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    giveaways = relationship("TableGiveaway", back_populates="steam_item")


class TableGiveaway(Base):
    __tablename__ = 'giveaway'
    giveaway_id = Column(String(10), primary_key=True, nullable=False)
    steam_id = Column(Integer, ForeignKey('steam_item.steam_id'), primary_key=True)
    giveaway_uri = Column(String(200), nullable=False)
    user = Column(String(40), nullable=False)
    giveaway_created_at = Column(DateTime(timezone=True), nullable=False)
    giveaway_ended_at = Column(DateTime(timezone=True), nullable=False)
    cost = Column(Integer(), nullable=False)
    copies = Column(Integer(), nullable=False)
    contributor_level = Column(Integer(), nullable=False)
    entered = Column(Boolean(), nullable=False)
    won = Column(Boolean(), nullable=False)
    game_entries = Column(Integer(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    steam_item = relationship("TableSteamItem", back_populates="giveaways")

    __mapper_args__ = {"eager_defaults": True}

    @classmethod
    def unix_timestamp_to_utc_datetime(cls, timestamp):
        return datetime.utcfromtimestamp(timestamp)

    @classmethod
    def upsert_giveaway(cls, giveaway, entered):
        with Session(engine) as session:
            result = session.query(TableGiveaway).filter_by(giveaway_id=giveaway.giveaway_game_id,
                                                            steam_id=giveaway.steam_app_id).all()
            if result:
                steam_id = result[0].steam_id
            else:
                item = TableSteamItem(
                    steam_id=giveaway.steam_app_id,
                    steam_url=giveaway.steam_url,
                    game_name=giveaway.game_name)
                session.merge(item)
                session.flush()
                steam_id = item.steam_id

            g = TableGiveaway(
                giveaway_id=giveaway.giveaway_game_id,
                steam_id=steam_id,
                giveaway_uri=giveaway.giveaway_uri,
                user=giveaway.user,
                giveaway_created_at=TableGiveaway.unix_timestamp_to_utc_datetime(giveaway.time_created_timestamp),
                giveaway_ended_at=TableGiveaway.unix_timestamp_to_utc_datetime(giveaway.time_remaining_timestamp),
                cost=giveaway.cost,
                copies=giveaway.copies,
                contributor_level=giveaway.contributor_level,
                entered=entered,
                won=False,
                game_entries=giveaway.game_entries)

            session.merge(g)
            session.commit()


if not database_exists(engine.url):
    create_database(engine.url)
    # emitting DDL
    mapper_registry.metadata.create_all(engine)
    Base.metadata.create_all(engine)
else:
    # Connect the database if exists.
    engine.connect()

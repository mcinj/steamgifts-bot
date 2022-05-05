from sqlalchemy import create_engine, Integer, String, Column, Table, \
    MetaData, DateTime, Numeric, Enum, Boolean, TIMESTAMP, func
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.orm import registry
from datetime import datetime
import pytz

mapper_registry = registry()
mapper_registry.metadata
Base = mapper_registry.generate_base()
engine = create_engine('sqlite:///../config/sqlite.db', echo=True)


class TableNotification(Base):
    __tablename__ = 'notification'
    id = Column(Integer, primary_key=True, nullable=False)
    type = Column(String(50), nullable=False)
    message = Column(String(300), nullable=False)
    medium = Column(String(50), nullable=False)
    success = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __mapper_args__ = {"eager_defaults": True}


class TableGiveaway(Base):
    __tablename__ = 'giveaway'
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String(200), nullable=False)
    game_id = Column(String(10), nullable=False)
    entries = Column(Integer(), nullable=False)
    giveaway_created = Column(DateTime(timezone=True), nullable=False)
    giveaway_ended = Column(DateTime(timezone=True), nullable=False)
    cost = Column(Integer(), nullable=False)
    copies = Column(Integer(), nullable=False)
    entered = Column(Boolean(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    added_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __mapper_args__ = {"eager_defaults": True}

    @classmethod
    def unix_timestamp_to_utc_datetime(cls, timestamp):
        return datetime.utcfromtimestamp(timestamp)


if not database_exists(engine.url):
    create_database(engine.url)
    # emitting DDL
    mapper_registry.metadata.create_all(engine)
    Base.metadata.create_all(engine)
else:
    # Connect the database if exists.
    engine.connect()
from sqlalchemy import Integer, String, Column, DateTime, Boolean, func, ForeignKey
from sqlalchemy.orm import registry, relationship

mapper_registry = registry()
metadata = mapper_registry.metadata
Base = mapper_registry.generate_base()


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
    game_entries = Column(Integer(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    steam_item = relationship("TableSteamItem", back_populates="giveaways")

    __mapper_args__ = {"eager_defaults": True}

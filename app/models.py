from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Bot(Base):
    __tablename__ = "bots"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    mastodon_token = Column(String(500), nullable=False)
    mastodon_account = Column(String(200), nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    schedule_times = Column(JSON, default=list, nullable=False)  # e.g. ["09:00", "18:00"]
    max_items = Column(Integer, default=5, nullable=False)
    use_ai = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    feeds = relationship("Feed", back_populates="bot", cascade="all, delete-orphan")
    runs = relationship("Run", back_populates="bot", cascade="all, delete-orphan")


class Feed(Base):
    __tablename__ = "feeds"

    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=False)
    url = Column(String(500), nullable=False)
    name = Column(String(200), nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    max_per_run = Column(Integer, default=10, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    bot = relationship("Bot", back_populates="feeds")


class Run(Base):
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    success = Column(Boolean, default=False, nullable=False)
    message = Column(Text, nullable=True)
    items_count = Column(Integer, default=0, nullable=False)

    bot = relationship("Bot", back_populates="runs")


from sqlalchemy import *
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    ...


class User(Base):
    __tablename__ = 'user'
    telegram_id = Column(BIGINT, primary_key=True, autoincrement=False, nullable=False)
    hash = Column(VARCHAR(40), nullable=True)
    email = Column(String, nullable=True, unique=True)
    remainder = Column(Boolean, default=True)


class Habit(Base):
    __tablename__ = 'habit'
    completed = Column(Boolean, default=False)
    progress = Column(Integer, default=0)
    border_progress = Column(Integer, default=21)

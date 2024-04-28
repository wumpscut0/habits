import pytz
from sqlalchemy import *
from sqlalchemy.orm import DeclarativeBase, relationship
from config import MAX_NAME_LENGTH, MAX_DESCRIPTION_LENGTH, MAX_EMAIL_LENGTH
from datetime import time, tzinfo

class Base(DeclarativeBase):
    ...


class User(Base):
    __tablename__ = 'user'
    telegram_id = Column(BIGINT, primary_key=True, autoincrement=False, nullable=False)
    hash = Column(String, nullable=True)
    email = Column(VARCHAR(MAX_EMAIL_LENGTH), nullable=True, unique=True)
    notifications = Column(Boolean, default=True)
    notification_time = Column(Time, default=time(20, 0, tzinfo=pytz.utc))
    habit = Column(Integer, ForeignKey('habit.id'))

    habits = relationship('Habit')


class Habit(Base):
    __tablename__ = 'habit'
    id = Column(Integer, primary_key=True)
    name = Column(VARCHAR(MAX_NAME_LENGTH), nullable=False)
    description = Column(VARCHAR(MAX_DESCRIPTION_LENGTH), default='No description')
    completed = Column(Boolean, default=False)
    progress = Column(Integer, default=0)
    border_progress = Column(Integer, default=21)

    user_id = Column(Integer, ForeignKey('user.telegram_id'), nullable=False)

    def as_dict_(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.c.columns}

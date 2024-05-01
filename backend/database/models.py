import pytz
from datetime import time

from sqlalchemy import *
from sqlalchemy.orm import DeclarativeBase, relationship

from backend import config

MAX_EMAIL_LENGTH = config.get('limitations', 'MAX_EMAIL_LENGTH')
MAX_NAME_LENGTH = config.get('limitations', 'MAX_NAME_LENGTH')
MAX_DESCRIPTION_LENGTH = config.get('limitations', 'MAX_DESCRIPTION_LENGTH')


class Base(DeclarativeBase):
    ...


class UserORM(Base):
    __tablename__ = 'user'
    telegram_id = Column(BIGINT, primary_key=True, autoincrement=False, nullable=False)
    hash = Column(String, nullable=True)
    email = Column(VARCHAR(MAX_EMAIL_LENGTH), nullable=True, unique=True)
    notifications = Column(Boolean, default=True)
    notification_time = Column(Time, default=time(20, 0, tzinfo=pytz.utc))
    target = Column(Integer, ForeignKey('target.id'))

    targets = relationship('HabitORM')


class TargetORM(Base):
    __tablename__ = 'target'
    id = Column(Integer, primary_key=True)
    name = Column(VARCHAR(MAX_NAME_LENGTH), nullable=False)
    description = Column(VARCHAR(MAX_DESCRIPTION_LENGTH), default='No description')
    completed = Column(Boolean, default=False)
    progress = Column(Integer, default=0)
    border_progress = Column(Integer, default=21)

    user_id = Column(Integer, ForeignKey('user.telegram_id'), nullable=False)

    def as_dict_(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.c.columns}

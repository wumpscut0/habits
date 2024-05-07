import pytz
from datetime import time, datetime, UTC

from sqlalchemy import *
from sqlalchemy.orm import DeclarativeBase, relationship

from backend.utils import config

MAX_EMAIL_LENGTH = config.getint('limitations', 'MAX_EMAIL_LENGTH')
MAX_NAME_LENGTH = config.getint('limitations', 'MAX_NAME_LENGTH')
MAX_DESCRIPTION_LENGTH = config.getint('limitations', 'MAX_DESCRIPTION_LENGTH')
DEFAULT_REMAINING_HOUR = config.getint('limitations', "DEFAULT_REMAINING_HOUR")


class Base(DeclarativeBase):
    ...


class UserORM(Base):
    __tablename__ = 'user'
    telegram_id = Column(BIGINT, primary_key=True, autoincrement=False, nullable=False)
    hash = Column(String, nullable=True)
    email = Column(VARCHAR(MAX_EMAIL_LENGTH), nullable=True, unique=True)
    notifications = Column(Boolean, default=True)
    notification_time = Column(Time, default=time(DEFAULT_REMAINING_HOUR, 0, tzinfo=pytz.utc))
    # target_id = Column(Integer, ForeignKey('target.id'))

    targets = relationship('TargetORM')


class TargetORM(Base):
    __tablename__ = 'target'
    id = Column(Integer, primary_key=True)
    create_datetime = Column(DateTime, default=datetime.now(UTC))
    completed_datetime = Column(DateTime)

    name = Column(VARCHAR(MAX_NAME_LENGTH), nullable=False)
    description = Column(VARCHAR(MAX_DESCRIPTION_LENGTH))
    completed = Column(Boolean, default=False)
    progress = Column(Integer, default=0)
    border_progress = Column(Integer, default=21)

    user_id = Column(Integer, ForeignKey('user.telegram_id'), nullable=False)

    def as_dict_(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.c.columns}

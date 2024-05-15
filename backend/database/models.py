import pytz
from datetime import time, datetime

from sqlalchemy import Column, BIGINT, String, VARCHAR, Boolean, Time, Integer, DateTime, ForeignKey
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
    id = Column(BIGINT, primary_key=True, autoincrement=False, nullable=False)
    hash = Column(String, nullable=True)
    email = Column(VARCHAR(MAX_EMAIL_LENGTH), nullable=True, unique=True)
    notifications = Column(Boolean, default=True)
    notification_time = Column(Time, default=time(DEFAULT_REMAINING_HOUR, 0, tzinfo=pytz.utc))

    targets = relationship('TargetORM')

    def as_dict_(self):
        data = {}
        for column in self.__table__.columns:
            if column.name == "notification_time":
                time_ = getattr(self, column.name)
                data[column.name] = {
                    "hour": time_.hour,
                    "minute": time_.minute
                }
            else:
                data[column.name] = getattr(self, column.name)
        return data


class TargetORM(Base):
    __tablename__ = 'target'
    id = Column(Integer, primary_key=True)
    create_datetime = Column(DateTime, default=datetime.now())
    completed_datetime = Column(DateTime)

    name = Column(VARCHAR(MAX_NAME_LENGTH), nullable=False)
    description = Column(VARCHAR(MAX_DESCRIPTION_LENGTH))
    completed = Column(Boolean, default=False)
    progress = Column(Integer, default=0)
    border_progress = Column(Integer, default=21)

    user_id = Column(BIGINT, ForeignKey('user.id'), nullable=False)

    def as_dict_(self):
        data = {}
        for column in self.__table__.columns:
            if column.name == "create_datetime":
                datetime_ = getattr(self, column.name)
                data[column.name] = datetime_.strftime("%d.%m.%y %H:%M:%S")
            elif column.name == "completed_datetime":
                datetime_ = getattr(self, column.name)
                if datetime_ is not None:
                    data[column.name] = datetime_.strftime("%d.%m.%y %H:%M:%S")
            else:
                data[column.name] = getattr(self, column.name)
        return data

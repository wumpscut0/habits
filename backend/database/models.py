from sqlalchemy import *
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    ...


class User(Base):
    __tablename__ = 'user'
    telegram_id = Column(BIGINT, nullable=False)
    nickname = Column(VARCHAR(10), nullable=False)
    login = Column(VARCHAR(10), primary_key=True, nullable=False)
    password = Column(String, nullable=True)

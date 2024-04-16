from sqlalchemy import *
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    ...


class User(Base):
    __tablename__ = 'user'
    id = Column(BIGINT, primary_key=True, unique=True, autoincrement=False, nullable=False)
    nickname = Column(VARCHAR(10), nullable=False)
    login = Column(VARCHAR(10), unique=True, nullable=False)
    hash = Column(String, nullable=True)

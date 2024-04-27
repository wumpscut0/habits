from sqlalchemy import *
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    ...


class User(Base):
    __tablename__ = 'user'
    telegram_id = Column(BIGINT, primary_key=True, autoincrement=False, nullable=False)
    hash = Column(VARCHAR(40), nullable=True)
    email = Column(String, nullable=True, unique=True)
    notifications = Column(Boolean, default=True)
    habit = Column(Integer, ForeignKey('habit.id'))

    habits = relationship('Habit')


class Habit(Base):
    __tablename__ = 'habit'
    id = Column(Integer, primary_key=True)
    name = Column(VARCHAR(30), nullable=False)
    description = Column(VARCHAR(150), default='No description')
    completed = Column(Boolean, default=False)
    progress = Column(Integer, default=0)
    border_progress = Column(Integer, default=21)

    user_id = Column(Integer, ForeignKey('user.telegram_id'), nullable=False)

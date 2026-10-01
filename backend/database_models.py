from datetime import datetime

from sqlalchemy import Column, String, DateTime, Integer

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    picture = Column(String, nullable=True)


class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(String, primary_key=True)
    title = Column(String, default="Untitled Meeting")
    host_user_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    status = Column(String, default="waiting")


class Participant(Base):
    __tablename__ = "participants"

    id = Column(String, primary_key=True)
    meeting_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)
    left_at = Column(DateTime, nullable=True)

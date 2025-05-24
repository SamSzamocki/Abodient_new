from sqlalchemy import create_engine, Column, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os

# Get database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/postgres")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class ConversationMessage(Base):
    __tablename__ = "conversation_messages"
    id = Column(String, primary_key=True)
    session_id = Column(String, index=True)
    sender = Column(String)  # 'user' or 'ai'
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class SessionMemory(Base):
    __tablename__ = "session_memory"
    session_id = Column(String, primary_key=True)
    memory_json = Column(Text)  # Store memory as a JSON string

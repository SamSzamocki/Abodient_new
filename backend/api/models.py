from sqlalchemy import create_engine, Column, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

# Update this with your actual database credentials
DATABASE_URL = "postgresql://user:password@localhost:5432/yourdb"

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

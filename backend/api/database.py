from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session
from models import ConversationMessage, SessionMemory
import uuid
from datetime import datetime
import sys
import json

def create_message(db: Session, session_id: str, sender: str, message: str):
    """
    Create a new chat message in the database
    """
    try:
        db_message = ConversationMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            sender=sender,
            message=message,
            timestamp=datetime.utcnow()
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        print(f"[DEBUG] Message committed for session {session_id}", file=sys.stderr)
        return db_message
    except Exception as e:
        print(f"[ERROR] Failed to commit message: {e}", file=sys.stderr)
        raise

def get_chat_history(db: Session, session_id: str, limit: int = 50):
    """
    Retrieve chat history for a given session
    """
    return db.query(ConversationMessage)\
        .filter(ConversationMessage.session_id == session_id)\
        .order_by(ConversationMessage.timestamp.desc())\
        .limit(limit)\
        .all()

def get_session_memory(db: Session, session_id: str):
    record = db.query(SessionMemory).filter(SessionMemory.session_id == session_id).first()
    if record and record.memory_json:
        return json.loads(record.memory_json)
    return {}

def set_session_memory(db: Session, session_id: str, memory: dict):
    memory_json = json.dumps(memory)
    record = db.query(SessionMemory).filter(SessionMemory.session_id == session_id).first()
    if record:
        record.memory_json = memory_json
    else:
        record = SessionMemory(session_id=session_id, memory_json=memory_json)
        db.add(record)
    db.commit()

def get_db():
    """
    Database session dependency
    """
    from models import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 
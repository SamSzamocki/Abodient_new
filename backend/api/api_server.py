import os
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from database import get_db, create_message, get_chat_history
from models import Base, engine
from agents.classifier import run_classifier_agent as classify
from otel_config import setup_telemetry
from sqlalchemy.orm import Session

# Initialize OpenTelemetry BEFORE importing other modules
setup_telemetry()

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Allow CORS from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Dependency to check API key
API_KEY = os.getenv("API_KEY", "changeme")
def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")

@app.get("/")
async def root():
    return {"hello": "abodient"}

# ---------- endpoints ----------
from pydantic import BaseModel
from agents.context_agent import run_context_agent
from agents.main_agent import handle_message
from agents.contract_agent import run_contract_agent as check_contract

class TextItem(BaseModel):
    session_id: str
    text: str

@app.post("/classify")
async def classify_ep(item: TextItem, api_key: str = Depends(verify_api_key)):
    """
    Given tenant text, return urgency & responsibility.
    """
    return classify(item.text)

@app.post("/context")
def context_ep(item: TextItem, api_key: str = Depends(verify_api_key)):
    return run_context_agent(item.text)

@app.post("/main-agent")
async def main_agent_ep(item: TextItem, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    # Store user message
    create_message(db, item.session_id, "user", item.text)
    
    # Fetch last 5 messages for context (in chronological order)
    history = get_chat_history(db, item.session_id, limit=5)
    formatted_history = [
        {"role": msg.sender, "content": msg.message} for msg in reversed(history)
    ]

    # DEBUG: Print what history we're actually passing
    print(f"[DEBUG API] Raw history from DB ({len(history)} messages):")
    for i, msg in enumerate(history):
        print(f"  {i}: {msg.sender}: {msg.message[:100]}...")
    
    print(f"[DEBUG API] Formatted history being passed to main agent ({len(formatted_history)} messages):")
    for i, msg in enumerate(formatted_history):
        print(f"  {i}: {msg['role']}: {msg['content'][:100]}...")
    
    # Use the actual main agent workflow
    response = handle_message(db, item.session_id, item.text, formatted_history)
    
    # Store AI response
    chat_output = response.get("chat_output", "")
    create_message(db, item.session_id, "ai", chat_output)
    
    return response

@app.post("/contract")
async def contract_ep(item: TextItem, api_key: str = Depends(verify_api_key)):
    return check_contract(item.text)

@app.get("/chat-history/{session_id}")
async def get_chat_history_ep(session_id: str, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    """
    Retrieve chat history for a given session
    """
    messages = get_chat_history(db, session_id)
    return [{"sender": msg.sender, "message": msg.message, "timestamp": msg.timestamp} for msg in messages]





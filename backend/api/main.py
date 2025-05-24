from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
from sqlalchemy.orm import Session
from database import get_db, create_message, get_chat_history
from models import Base, engine
from langfuse.callback import CallbackHandler
from langchain_community.chat_models import ChatOpenAI

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
from agents.classifier import classify
from agents.context_agent import run_context_agent
from agents.main_agent import handle_message
from agents.contract_agent import search_contract as check_contract

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

    # Get AI response, passing history
    langfuse_handler = CallbackHandler(
        public_key="pk-lf-d9a88b84-cdab-44eb-bada-98f2c8567ab7",
        secret_key="sk-lf-06a5516a-d683-44d4-b2b2-418ad43429f3",
        host="https://cloud.langfuse.com"
    )
    llm = ChatOpenAI(model_name="gpt-3.5-turbo")
    response = llm.invoke(item.text, config={"callbacks": [langfuse_handler]})
    
    # Store AI response
    create_message(db, item.session_id, "ai", response.content)
    
    return {"chat_output": response.content}

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





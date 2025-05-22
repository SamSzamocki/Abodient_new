from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
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
async def main_agent_ep(item: TextItem, api_key: str = Depends(verify_api_key)):
    return handle_message(session_id=item.session_id, text=item.text)

@app.post("/contract")
async def contract_ep(item: TextItem, api_key: str = Depends(verify_api_key)):
    return check_contract(item.text)





from fastapi import FastAPI
app = FastAPI()

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
async def classify_ep(item: TextItem):
    """
    Given tenant text, return urgency & responsibility.
    """
    return classify(item.text)

@app.post("/context")
def context_ep(item: TextItem):
    return run_context_agent(item.text)


@app.post("/main-agent")
async def main_agent_ep(item: TextItem):
    return handle_message(session_id=item.session_id, text=item.text)


@app.post("/contract")
async def contract_ep(item: TextItem):
    return check_contract(item.text)





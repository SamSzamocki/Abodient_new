from langchain.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from .context_agent import run_context_agent
from .contract_agent import run_contract_agent  
from .classifier import run_classifier_agent

# We'll store the current session_id globally for tools to access
_current_session_id = None

def set_current_session_id(session_id: str):
    """Set the current session ID for tools to use"""
    global _current_session_id
    _current_session_id = session_id

def get_current_session_id() -> str:
    """Get the current session ID"""
    return _current_session_id or "default_session"

class ContextAgentInput(BaseModel):
    query: str = Field(description="The user query summary to get context for")

class ContextAgentTool(BaseTool):
    name: str = "ContextAgent"
    description: str = "Always call this tool as your first step, to check if more context or clarification is required"
    args_schema: Type[BaseModel] = ContextAgentInput

    def _run(self, query: str) -> str:
        """Execute the context agent with shared memory"""
        try:
            session_id = get_current_session_id()
            result = run_context_agent(query, session_id)
            return str(result)
        except Exception as e:
            return f"Error calling context agent: {str(e)}"

class ContractAgentInput(BaseModel):
    query: str = Field(description="The vector search query to check contractual position")

class ContractAgentTool(BaseTool):
    name: str = "contractAgent"
    description: str = "Used to check the contractual position on a tenants query"
    args_schema: Type[BaseModel] = ContractAgentInput

    def _run(self, query: str) -> str:
        """Execute the contract agent with shared memory"""
        try:
            session_id = get_current_session_id()
            result = run_contract_agent(query, session_id)
            return str(result)
        except Exception as e:
            return f"Error calling contract agent: {str(e)}"

class ClassifierAgentInput(BaseModel):
    query: str = Field(description="The vector search query to verify urgency level")

class ClassifierAgentTool(BaseTool):
    name: str = "classifierAgent"
    description: str = "Used to verify the level of urgency and advisable next steps"
    args_schema: Type[BaseModel] = ClassifierAgentInput

    def _run(self, query: str) -> str:
        """Execute the classifier agent with shared memory"""
        try:
            session_id = get_current_session_id()
            result = run_classifier_agent(query, session_id)
            return str(result)
        except Exception as e:
            return f"Error calling classifier agent: {str(e)}"

def create_tools_for_session(session_id: str):
    """Create tools with the proper session_id"""
    return [
        ContextAgentTool(session_id=session_id),
        ContractAgentTool(session_id=session_id),
        ClassifierAgentTool(session_id=session_id)
    ]

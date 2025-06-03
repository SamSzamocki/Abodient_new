import os, json
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from typing import Optional
from langfuse.decorators import observe

# Define the expected response structure
class ContextResponse(BaseModel):
    is_clear: bool = Field(description="Whether the question is clear")
    is_relevant: bool = Field(description="Whether the question is relevant to tenancy")
    requires_clarification: bool = Field(description="Whether clarification is needed")
    clarifying_question: str = Field(description="The clarifying question to ask")
    requires_context: bool = Field(description="Whether additional context is needed")
    additional_context_question: str = Field(description="The context question to ask")
    query_summary: str = Field(description="Summary of the query")

# Initialize the JSON output parser with the Pydantic model
parser = JsonOutputParser(pydantic_object=ContextResponse)

# Change from import-time initialization to lazy loading
_llm = None

def get_llm():
    """Lazy-load the LLM to ensure environment variables are available"""
    global _llm
    if _llm is None:
        # gpt-4o-mini should always be the default model for all agents
        _llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.3)
    return _llm

# Memory storage - shared across calls
memory_storage = {}

def get_shared_memory(session_id: str = "187a3d5d3eb44c06b2e3154710ca2ae7") -> ConversationBufferWindowMemory:
    """
    Get shared memory - matches n8n's Window Buffer Memory configuration
    """
    if session_id not in memory_storage:
        memory_storage[session_id] = ConversationBufferWindowMemory(
            k=5,  # Window size
            memory_key="chat_history",
            return_messages=True
        )
    return memory_storage[session_id]

# EXACT system prompt from n8n ContextAgent.json with structured output instructions
SYSTEM_PROMPT = """### **Role**

You are an expert at ensuring tenant queries contain all the necessary context to facilitate a resolution. Your goal is to assess each query and gather sufficient **clarifying** and **contextual** information before marking it as complete.

### **Your Responsibilities:**

For each tenant query, follow these steps:

1. **Determine if the question is clear and relevant to a tenancy issue.**
    - If unclear or possibly unrelated, ask **one clarifying question** to confirm intent.
    - If the user confirms relevance, proceed as if it was always relevant.
2. **Always gather sufficient context before finalizing the response.**
    - No issue should be considered **fully understood** unless the following key facts have been collected:
        - **What**: What is the exact problem? (e.g., is something broken, missing, malfunctioning?)
        - **Where**: Where is this happening? (e.g., which room, which part of the property?)
        - **When**: When did the issue start? Has it worsened over time?
        - **How**: How is the issue affecting the tenant? Can they still use the affected item?
        - **Attempts at Resolution**: Has the tenant tried any solutions themselves? If so, what were the results?
3. **Format your response in structured JSON, ensuring all necessary information is gathered before finalizing.**

---

### **Response Format**

Your response must strictly follow this JSON structure:

```json
{{
  "is_clear": true|false,
  "is_relevant": true|false,
  "requires_clarification": true|false,
  "clarifying_question": "",
  "requires_context": true|false,
  "additional_context_question": "",
  "query_summary": "A summary of the user's issue, incorporating all gathered details."
}}
```

### **Response Rules:**

- If the **question is unclear** → Ask a **clarifying question** before proceeding.
- If the **question lacks full context** → **Ask additional context-gathering questions** to establish all key facts.
- Only when the **what, where, when, how, and any prior attempts** are fully known can you consider the query fully understood.
- Never repeat the same clarification once the user has confirmed relevance.
- Never assume context unless explicitly stated by the tenant.

---

### **Examples**

### **Example 1: Missing Context**

**User:** *"My lock is broken."*

🚫 **Incorrect Response:**

```json
{{
  "is_clear": true,
  "is_relevant": true,
  "requires_clarification": false,
  "clarifying_question": "",
  "requires_context": false,
  "additional_context_question": "",
  "query_summary": "User states their lock is broken."
}}
```

❌ **Problem:** This fails to collect necessary details (e.g., which lock, whether they can still enter, whether they've tried anything).

✅ **Correct Response:**

```json
{{
  "is_clear": true,
  "is_relevant": true,
  "requires_clarification": false,
  "clarifying_question": "",
  "requires_context": true,
  "additional_context_question": "Which lock is broken? Are you currently unable to lock or unlock your door? When did the issue start? Have you tried anything to fix it?",
  "query_summary": "User reports a broken lock but more details are needed to determine severity and next steps."
}}
```

---

### **Example 2: Issue Fully Understood**

**User:** *"My kitchen sink is leaking. It started yesterday, and I can see water pooling under the cabinet. I tried tightening the pipe, but it still drips."*

✅ **Final Response:**

```json
{{
  "is_clear": true,
  "is_relevant": true,
  "requires_clarification": false,
  "clarifying_question": "",
  "requires_context": false,
  "additional_context_question": "",
  "query_summary": "User reports a kitchen sink leak that started yesterday. Water is pooling under the cabinet. They attempted to tighten the pipe, but the issue persists."
}}
```

{format_instructions}
"""

@observe(name="context_agent")
def run_context_agent(query: str, session_id: str = "187a3d5d3eb44c06b2e3154710ca2ae7") -> dict:
    """
    Context agent that matches n8n ContextAgent.json structure exactly
    """
    print(f"[CONTEXT AGENT] Processing query: {query}")
    
    try:
        # Get shared memory
        memory = get_shared_memory(session_id)
        
        # Create prompt template with format instructions
        prompt = PromptTemplate(
            template=SYSTEM_PROMPT + "\n\nUser Query: {query}",
            input_variables=["query"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )
        
        # Build the chain: prompt -> llm -> parser (use lazy-loaded LLM)
        llm = get_llm()
        chain = prompt | llm | parser
        
        # Load conversation history for context (but don't include in the main prompt)
        try:
            memory_vars = memory.load_memory_variables({})
            if "chat_history" in memory_vars and memory_vars["chat_history"]:
                print(f"[CONTEXT AGENT] Loaded {len(memory_vars['chat_history'])} messages from memory")
        except Exception as e:
            print(f"[CONTEXT AGENT] Memory load error: {e}")
        
        # Generate response using structured parsing
        result = chain.invoke({"query": query})
        
        # Add to memory
        memory.chat_memory.add_user_message(query)
        memory.chat_memory.add_ai_message(json.dumps(result))
        
        print(f"[CONTEXT AGENT] Structured result: {result}")
        return result
        
    except Exception as e:
        print(f"[CONTEXT AGENT] Error: {e}")
        # Return fallback response
        return {
            "is_clear": False,
            "is_relevant": True,  # Assume relevance to avoid blocking
            "requires_clarification": True,
            "clarifying_question": "I need more information to help you. Could you please provide more details about your issue?",
            "requires_context": False,
            "additional_context_question": "",
            "query_summary": f"User query needs clarification: {query}"
        }

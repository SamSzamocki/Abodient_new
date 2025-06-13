import os, json
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field
from typing import Optional
from langfuse.decorators import observe
from memory.scoped_memory_manager import get_agent_memory, get_dual_memory_for_agent
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA

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

# Note: Replaced global memory_storage with scoped memory manager
# This ensures context agent only sees main agent ↔ context agent conversations

def get_shared_memory(session_id: str = "187a3d5d3eb44c06b2e3154710ca2ae7") -> ConversationBufferWindowMemory:
    """
    Get memory for main agent ↔ context agent conversations only.
    Now uses scoped memory manager to ensure conversation isolation.
    """
    return get_agent_memory(session_id, "context")

# Note this system prompt has been updated and improves upon the n8n prompt.
SYSTEM_PROMPT = """### **Role**

You are an expert at ensuring tenant property queries contain all the necessary context to facilitate a resolution. You will receive summaries of user queries. Your goal is to assess these summaries and continue to gather sufficient **clarifying** and **contextual** information until the completeness criteria are met. Even though you are receiving third person summaries, you must respond as though you are actually conversing with the user. 

*Tone of voice*: Be friendly, professional, polite, slightly sympathetic, light-hearted, act like a cheerful customer services rep. Feel free to use emojis.

### **Your Responsibilities:**

For each tenant query you receive, follow these steps:

1. **Determine if the question is clear and relevant to a tenancy issue.**
    - If unclear or possibly unrelated to tenancy issues, ask **one clarifying question** to confirm intent of the query.
    - If the user's responses indicate that it is relevant to tenancy related issues, move to the next step proceed as if it was always relevant.
2. **Ask clarifying questions until the query is **fully understood** and the **completeness criteria** are met. You can ask multiple clarifying questions if needed, in cases where it would help the interaction feel more natural.
    - **Completeness criteria**: No issue should be considered **fully understood** unless the following key facts have been collected:
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
  "is_clear": <true|false>,
  "is_relevant": <true|false>,
  "requires_clarification": <true|false>,
  "clarifying_question": "",
  "requires_context": <true|false>,
  "additional_context_question": "",
  "query_summary": "A summary of the user's issue, incorporating all gathered details up to the current point of the interaction."
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
  "additional_context_question": "Oh I'm sorry to hear that! In order to assist you further, I'll need to gather a little more context :). Which lock is broken? Are you currently unable to lock or unlock your door? When did the issue start? Have you tried anything to fix it?",
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

---

### **Example 3: Heating Issue – Missing Details**

**User:** *"My radiators are cold."*

🚫 **Incorrect Response:**

```json
{{
  "is_clear": true,
  "is_relevant": true,
  "requires_clarification": false,
  "clarifying_question": "",
  "requires_context": false,
  "additional_context_question": "",
  "query_summary": "User reports cold radiators."
}}
```

❌ **Problem:** Does not ask where the radiators are, when it started, or if any troubleshooting was attempted.

✅ **Correct Response:**

```json
{{
  "is_clear": true,
  "is_relevant": true,
  "requires_clarification": false,
  "clarifying_question": "",
  "requires_context": true,
  "additional_context_question": "Oh no, chilly rooms are no fun! 🥶 To help me warm things up again, could you let me know which rooms are affected, when the radiators stopped warming up, and whether you've tried bleeding them or adjusting the thermostat?",
  "query_summary": "User reports radiators are cold but needs location, timing and attempted fixes."
}}
```

---

### **Example 4: Broken Window – Impact Unknown**

**User:** *"A window in my bedroom is cracked."*

🚫 **Incorrect Response:**

```json
{{
  "is_clear": true,
  "is_relevant": true,
  "requires_clarification": false,
  "clarifying_question": "",
  "requires_context": false,
  "additional_context_question": "",
  "query_summary": "Bedroom window cracked."
}}
```

❌ **Problem:** Fails to ask how severe the crack is or if the tenant can still close the window.

✅ **Correct Response:**

```json
{{
  "is_clear": true,
  "is_relevant": true,
  "requires_clarification": false,
  "clarifying_question": "",
  "requires_context": true,
  "additional_context_question": "Yikes, that doesn't sound safe! 😟 Just so I can gauge how urgent this is, is the crack large or spreading? Can you still open and close the window securely, and when did you first notice the damage?",
  "query_summary": "User reports cracked bedroom window; more details required regarding severity and timeline."
}}
```

---

### **Example 5: Decorating Permission – Clarification Needed**

**User:** *"Can I paint my living-room walls a different color?"*

✅ **Correct Response (needs clarification):**

```json
{{
  "is_clear": true,
  "is_relevant": true,
  "requires_clarification": false,
  "clarifying_question": "",
  "requires_context": true,
  "additional_context_question": "That sounds like a fun makeover! 🎨 Could you share what color you have in mind and whether you're able to repaint back to neutral when the tenancy ends? This helps us give accurate guidance.",
  "query_summary": "Tenant wants to repaint living-room walls; need specifics on color choice and reinstatement plan."
}}
```

---

### **Example 6: Completely Unrelated Question**

**User:** *"What's the best pizza topping?"*

✅ **Appropriate Response (irrelevant):**

```json
{{
  "is_clear": true,
  "is_relevant": false,
  "requires_clarification": true,
  "clarifying_question": "I might be a pizza fan too 🍕, but just to check—does your question relate to your tenancy or the property in any way? I'm here to help with rental-related issues!",
  "requires_context": false,
  "additional_context_question": "",
  "query_summary": "User asked a non-tenancy pizza preference question."
}}
```

---

### **Example 7: Noisy Neighbour – Specifics Missing**

**User:** *"My upstairs neighbour is stomping around all night."*

🚫 **Incorrect Response:**

```json
{{
  "is_clear": true,
  "is_relevant": true,
  "requires_clarification": false,
  "clarifying_question": "",
  "requires_context": false,
  "additional_context_question": "",
  "query_summary": "Neighbour noise issue."
}}
```

❌ **Problem:** Doesn't ask when the noise happens or whether the tenant has tried speaking to the neighbour.

✅ **Correct Response:**

```json
{{
  "is_clear": true,
  "is_relevant": true,
  "requires_clarification": false,
  "clarifying_question": "",
  "requires_context": true,
  "additional_context_question": "So sorry your sleep's being disturbed 😴💤. To figure out the best way to resolve this, could you tell me the usual times the noise occurs, how long it's been happening, and whether you've already spoken to the neighbour or left a polite note?",
  "query_summary": "Tenant reports noisy upstairs neighbour; need timing and prior actions taken."
}}
```

---

### **Example 8: Lost Keys – Missing Timeline & Attempts**

**User:** *"I lost my front-door keys."*

✅ **Correct Response (needs context):**

```json
{{
  "is_clear": true,
  "is_relevant": true,
  "requires_clarification": false,
  "clarifying_question": "",
  "requires_context": true,
  "additional_context_question": "Oh dear! 🔑😬 So we can sort this quickly, when did you misplace them, do you have a spare you can use for now, and have you already checked common areas or contacted a locksmith?",
  "query_summary": "Tenant lost front-door keys; need timeline and attempted solutions."
}}
```

---

### **Example 9: Mould Issue – Partially Understood**

**User:** *"There's mould in my bathroom."*

🚫 **Incorrect Response:**

```json
{{
  "is_clear": true,
  "is_relevant": true,
  "requires_clarification": false,
  "clarifying_question": "",
  "requires_context": false,
  "additional_context_question": "",
  "query_summary": "Bathroom mould reported."
}}
```

❌ **Problem:** Misses where exactly, how extensive, when noticed, and attempts to clean.

✅ **Correct Response:**

```json
{{
  "is_clear": true,
  "is_relevant": true,
  "requires_clarification": false,
  "clarifying_question": "",
  "requires_context": true,
  "additional_context_question": "I'm sorry to hear that—mould can be nasty! 😔 To tackle it effectively, could you tell me which parts of the bathroom are affected (ceiling, tiles, sealant?), when you first noticed it, and if you've tried any cleaning products so far?",
  "query_summary": "Bathroom mould noted; need precise location, start date, and tenant's cleaning attempts."
}}
```

---

### **Example 10: Power Outage – Clarification Needed**

**User:** *"The power keeps tripping in my flat."*

✅ **Correct Response (needs context):**

```json
{{
  "is_clear": true,
  "is_relevant": true,
  "requires_clarification": false,
  "clarifying_question": "",
  "requires_context": true,
  "additional_context_question": "That's frustrating! ⚡️😕 So I can figure out what's causing this, does it affect the whole flat or certain rooms? When did it start, and have you noticed any particular appliance causing the trip?",
  "query_summary": "Tenant experiencing repeated power trips; need scope, timing and trigger details."
}}
```

---

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
        
        # Create prompt template with memory and format instructions
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT + "\n\n{format_instructions}"),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "User Query: {query}")
        ])
        
        # Build the chain: prompt -> llm -> parser (use lazy-loaded LLM)
        llm = get_llm()
        
        # Load conversation history for context
        try:
            memory_vars = memory.load_memory_variables({})
            chat_history = memory_vars.get("chat_history", [])
            print(f"[CONTEXT AGENT] Using {len(chat_history)} messages from memory")
        except Exception as e:
            print(f"[CONTEXT AGENT] Memory load error: {e}")
            chat_history = []
        
        # Prepare the input for the chain
        chain_input = {
            "query": query,
            "chat_history": chat_history,
            "format_instructions": parser.get_format_instructions()
        }
        print(f"[CONTEXT AGENT] About to invoke LLM with query: {query[:100]}...")
        print(f"[CONTEXT AGENT] Chat history length: {len(chat_history)}")
        print(f"[CONTEXT AGENT] Format instructions length: {len(parser.get_format_instructions())} chars")
        
        # Generate response using manual LLM invocation and parsing
        try:
            # Create the full prompt manually
            print(f"[CONTEXT AGENT] Starting prompt formatting...")
            prompt_value = prompt.format_prompt(**chain_input)
            print(f"[CONTEXT AGENT] Prompt formatting successful, sending to LLM...")
            
            # Get the raw LLM response
            print(f"[CONTEXT AGENT] Invoking LLM...")
            raw_response = llm.invoke(prompt_value.to_messages())
            print(f"[CONTEXT AGENT] Raw LLM response received:")
            print(f"[CONTEXT AGENT] Response type: {type(raw_response)}")
            print(f"[CONTEXT AGENT] Response content: {raw_response.content}")
            
            # Now parse the response manually
            print(f"[CONTEXT AGENT] Attempting to parse JSON response...")
            result = parser.parse(raw_response.content)
            print(f"[CONTEXT AGENT] JSON parsing successful!")
            
        except Exception as parsing_error:
            print(f"[CONTEXT AGENT] Exception occurred: {type(parsing_error).__name__}: {parsing_error}")
            if 'raw_response' in locals():
                print(f"[CONTEXT AGENT] Raw response that failed to parse: {raw_response.content}")
            else:
                print(f"[CONTEXT AGENT] Error occurred before raw response was obtained")
                print(f"[CONTEXT AGENT] Available locals: {list(locals().keys())}")
            raise parsing_error
        
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


def get_dual_memory_for_context(session_id: str) -> tuple[ConversationBufferWindowMemory, ConversationBufferWindowMemory]:
    """
    Get dual memory access for context agent.
    
    Returns:
        Tuple of (user_memory, context_memory)
        - user_memory: User ↔ Main Agent conversations (actual user responses)
        - context_memory: Main Agent ↔ Context Agent conversations (structured summaries)
    """
    return get_dual_memory_for_agent(session_id, "context")


@observe(name="context_agent_dual_memory")
def run_context_agent_with_dual_memory(query: str, session_id: str = "187a3d5d3eb44c06b2e3154710ca2ae7") -> dict:
    """
    Enhanced context agent with dual memory access.
    
    This agent can see both:
    1. User ↔ Main Agent conversations (actual user responses with nuance)
    2. Main Agent ↔ Context Agent conversations (structured summaries)
    
    This allows it to track partial information provided across multiple turns.
    """
    print(f"[CONTEXT AGENT DUAL] Processing query: {query}")
    
    try:
        # Get both memory streams
        user_memory, context_memory = get_dual_memory_for_context(session_id)
        
        # Create enhanced prompt template with both memory streams
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT + "\n\n{format_instructions}"),
            ("system", "You have access to TWO conversation streams:\n1. USER CONVERSATIONS: Actual user messages with full detail and nuance\n2. AGENT CONVERSATIONS: Your structured conversation with the main agent\n\nUse BOTH streams to make informed decisions about what information has been gathered."),
            ("system", "USER CONVERSATION HISTORY:\n{user_history}"),
            ("system", "AGENT CONVERSATION HISTORY:\n{agent_history}"),
            ("human", "User Query: {query}")
        ])
        
        # Load conversation histories from both memory streams
        try:
            user_vars = user_memory.load_memory_variables({})
            user_history = user_vars.get("chat_history", [])
            
            context_vars = context_memory.load_memory_variables({})
            context_history = context_vars.get("chat_history", [])
            
            print(f"[CONTEXT AGENT DUAL] User memory: {len(user_history)} messages")
            print(f"[CONTEXT AGENT DUAL] Context memory: {len(context_history)} messages")
            
        except Exception as e:
            print(f"[CONTEXT AGENT DUAL] Memory load error: {e}")
            user_history = []
            context_history = []
        
        # Format conversation histories for the prompt
        user_history_text = "\n".join([
            f"{'User' if i % 2 == 0 else 'Main Agent'}: {msg.content if hasattr(msg, 'content') else str(msg)}"
            for i, msg in enumerate(user_history)
        ]) if user_history else "No user conversation history yet."
        
        agent_history_text = "\n".join([
            f"{'Main Agent' if i % 2 == 0 else 'Context Agent'}: {msg.content if hasattr(msg, 'content') else str(msg)}"
            for i, msg in enumerate(context_history)
        ]) if context_history else "No agent conversation history yet."
        
        # Prepare the input for the chain
        chain_input = {
            "query": query,
            "user_history": user_history_text,
            "agent_history": agent_history_text,
            "format_instructions": parser.get_format_instructions()
        }
        
        print(f"[CONTEXT AGENT DUAL] About to invoke LLM with enhanced context")
        print(f"[CONTEXT AGENT DUAL] User history length: {len(user_history_text)} chars")
        print(f"[CONTEXT AGENT DUAL] Agent history length: {len(agent_history_text)} chars")
        
        # Generate response using manual LLM invocation and parsing
        try:
            # Create the full prompt manually
            prompt_value = prompt.format_prompt(**chain_input)
            
            # Get the raw LLM response
            llm = get_llm()
            raw_response = llm.invoke(prompt_value.to_messages())
            print(f"[CONTEXT AGENT DUAL] Raw LLM response received")
            
            # Parse the response
            result = parser.parse(raw_response.content)
            print(f"[CONTEXT AGENT DUAL] JSON parsing successful!")
            
        except Exception as parsing_error:
            print(f"[CONTEXT AGENT DUAL] Exception occurred: {type(parsing_error).__name__}: {parsing_error}")
            if 'raw_response' in locals():
                print(f"[CONTEXT AGENT DUAL] Raw response that failed to parse: {raw_response.content}")
            raise parsing_error
        
        # Add to context memory (agent conversation)
        context_memory.chat_memory.add_user_message(query)
        context_memory.chat_memory.add_ai_message(json.dumps(result))
        
        print(f"[CONTEXT AGENT DUAL] Enhanced result: {result}")
        return result
        
    except Exception as e:
        print(f"[CONTEXT AGENT DUAL] Error: {e}")
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

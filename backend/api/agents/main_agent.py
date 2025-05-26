import os, json, sys
from langchain_openai import ChatOpenAI
from database import get_session_memory, set_session_memory
from langchain.memory import ConversationBufferWindowMemory
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from .tools import ContextAgentTool, ContractAgentTool, ClassifierAgentTool, set_current_session_id

# Initialize tools - these match the n8n tool configuration
tools = [
    ContextAgentTool(),
    ContractAgentTool(),
    ClassifierAgentTool()
]

# LLM configuration - matches n8n OpenAI Chat Model
llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.7)

# Shared memory storage - one memory per session_id
session_memories = {}

def get_shared_memory(session_id: str) -> ConversationBufferWindowMemory:
    """
    Get shared memory for a specific session - matches n8n's "Take from previous node automatically"
    """
    if session_id not in session_memories:
        session_memories[session_id] = ConversationBufferWindowMemory(
            k=5,  # Keep last 5 conversation turns
            memory_key="chat_history", 
            return_messages=True
        )
    return session_memories[session_id]

def create_main_agent(session_id: str) -> AgentExecutor:
    """
    Create the main agent with tools and memory - this replicates the n8n AI Agent structure
    """
    # Set the session ID for tools to use
    set_current_session_id(session_id)
    
    # Get shared memory for this specific session
    memory = get_shared_memory(session_id)
    
    # System prompt from n8n configuration - EXACT copy with typo fixed
    system_prompt = """***Role***
You are an expert property management agent acting on behalf of the landlord, to respond to queries that tenants have and take actions where appropriate. You must use your expertise, as well as the tools at your disposal to consider the context of the query, assessed severity/urgency, contractual position (if applicable), and then respond in the most helpful and friendly manner whilst respecting your legal obligation as a (stand in) landlord. 


***Tools***
*ContextAgent: *always* Call this tool as your first step, to check if more context or clarification is required
*contractAgent - Used to check the contractual position on a tenants query
*classifierAgent - Used to verify the level of urgency and advisable next steps

Remember, tools give valuable new information which will help you to provide the best response possible, make use of them as much as you can.

***Instructions***
Step 1: ALWAYS pass an up-to-date summary of the users query, directly to the ContextAgent tool and wait for the response. NEVER SKIP THIS STEP. You must not skip this step else you will fail. Check the Human/AI conversation history to generate a good summary to pass to the ContextAgent tool.
ALWAYS pass an up-to-date summary of the user's query to the ContextAgent tool and wait for the response. NEVER SKIP THIS STEP.
- If the response contains a clarifying question, output this clarifying question to the user and wait for their response.
- If the response contains an additional_context_question, output this additional context question to the user and wait for their response.
-After receiving a response from the user, send the updated query summary back to the ContextAgent again.
Repeat this process until the ContextAgent confirms that no further clarification or context is required.
-Only then proceed to Step 2.

- Step 2:
Using the summary of the tenant query, convert it into a concise vector search query

The query should be short, use only relevant keywords, and exclude unnecessary words.

Example good search query: "pet policy rental agreement"

Example bad search query: "What does my rental agreement say about pets?"

- Step 3: Send the vector search query to the contractAgent

- Step 4: Send the vector search query to the classifierAgent

- Step 5: Use the returned information from both contractAgent and classifierAgent to make an informed decision on how best to respond to the user.

- *Important*
you are attempting to help the user resolve their problem, but are representing the landlord. Therefore, you must speak in the voice of the landlord, upholding and fulfilling your duties where required to do so according to the contract and generally accepted practices between tenant/landlord relationships.

You may recommend a course of action to be taken on the landlords behalf, such as contacting a plumber, electrician, or any other profession typically employed to resolve tenancy issues. If you deem that this is required, CLEARLY STATE that this is what you will do in your response

Finally, NEVER tell the user to communicate with the landlord. YOU ARE the stand-in landlord, therefore telling them to do so is non-sensical. 

- **Tone**
Helpful, friendly, but professional

- **Output examples**

Example 1

User summary: User has a persistent issue with mould and has attempted to remove the mould to no avail.

contractAgent: The landlord is responsible for general upkeep and making the tenancy livable

classifierAgent: Mould is classed as an arguent issue as there are potential risks to the tenants health

Your Response: "Based on what you've told me, the contract states this issue is now the responsibility of the landlord and should be handled urgently. The landlord will be informed and I will arrange to have an expert sent round to investigate the issue and help you resolve it.

Example 2

User summary: There is a leaking roof that is causing water to drip into the tenant's bedroom. The tenant tried patching it with sealant but the leak remains.

contractAgent: Landlord is responsible for maintaining the structure and exterior of the property, including the roof.

classifierAgent: This issue is high urgency due to the potential for ongoing damage to the property and health/safety risks (e.g., mold, structural concerns).

Your Response: "According to your tenancy agreement, I'm responsible for keeping the roof in good repair to protect your living space. This sounds urgent, so I'll notify the landlord immediately and arrange to have a professional roofer inspect and repair the leak as soon as possible. Thank you for letting us know."

Example 3

User summary: The heating system is not working properly, and the tenant has no hot water or heating. They have tried resetting the boiler with no success.

contractAgent: The landlord's contractual obligations include providing a functioning heating and hot water system.

classifierAgent: Heating and hot water issues are considered urgent, especially if outside temperatures are low or it affects habitability.

Your Response:
"I understand you have no heating or hot water, and that's a serious concern. Under the rental agreement, the landlord is responsible for providing and maintaining a working heating system. I'll inform the landlord right away and arrange for a certified technician to come out and fix the issue as quickly as possible."

Example 4

User summary: Tenant would like to add decorations to the apartment and need to drill holes

contractAgent: The tenant must receive permission from the landlord before doing any decorative work. The tenant must also return the apartment to a normal state afterwards

classifierAgent: Decorations and internal modifications are low risk with no immediate action required, other than to seek permission from the landlord

Your Response: "Hanging your own decorations is permitted but only once permission from the landlord is sought. If you give me the full details of what you wish to hang up, I will request permission from the landlord for you. Thank you for keeping us updated."

Now Begin!"""

    # Create prompt template with memory placeholder
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # Create the agent
    agent = create_openai_tools_agent(llm, tools, prompt)
    
    # Create agent executor with memory
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True,
        max_iterations=10,
        early_stopping_method="generate"
    )
    
    return agent_executor

def handle_message(db, session_id: str, text: str, history=None) -> dict:
    """
    Main entry point - this replicates the n8n workflow orchestration
    Now properly uses the session_id parameter
    """
    print(f"[MAIN AGENT] Processing message for session {session_id}: {text}")
    
    # Create agent with shared memory for this specific session
    agent_executor = create_main_agent(session_id)
    
    # Execute the agent - this will automatically call tools based on the system prompt
    try:
        response = agent_executor.invoke({"input": text})
        agent_output = response["output"]
        
        # Parse the agent output to extract structured information
        result = {
            "chat_output": agent_output,
            "query_summary": text,
            "actions": []
        }
        
        print(f"[MAIN AGENT] Generated response for session {session_id}")
        return result
        
    except Exception as e:
        print(f"[MAIN AGENT] Error: {str(e)}")
        return {
            "chat_output": "I apologize, but I encountered an error processing your request. Please try again.",
            "query_summary": text,
            "actions": []
        }

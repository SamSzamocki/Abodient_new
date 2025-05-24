import os, json, sys
from langchain_openai import ChatOpenAI
from agents.context_agent import run_context_agent
from agents.classifier import classify
from agents.contract_agent import search_contract
from database import get_session_memory, set_session_memory
from langchain.memory import ConversationBufferMemory
from langfuse import Langfuse
from langfuse.callback import CallbackHandler

session_memories = {}
session_states = {}

langfuse = Langfuse(
    public_key="pk-lf-74330ae6-3669-413d-b773-0d5cf2fb20a6",
    secret_key="sk-lf-f9c1f478-c6a0-4e4d-be45-7b246a86c406",
    host="https://cloud.langfuse.com"  # Default, change if self-hosted
)

langfuse_handler = CallbackHandler(
    public_key="pk-lf-d9a88b84-cdab-44eb-bada-98f2c8567ab7",
    secret_key="sk-lf-06a5516a-d683-44d4-b2b2-418ad43429f3",
    host="https://cloud.langfuse.com"
)

llm = ChatOpenAI(model_name="gpt-4o-mini")

def handle_message(db, session_id: str, text: str, history=None) -> dict:
    """
    Main agent logic with memory. Handles clarification, context, and routes to tools.
    Returns a structured response with chat output, query summary, and actions.
    """
    # Set up memory for chat history (LangChain RAM memory)
    if session_id not in session_memories:
        session_memories[session_id] = ConversationBufferMemory(return_messages=True)
    memory = session_memories[session_id]

    # Set up state for extra info (clarification, query summary, etc.)
    if session_id not in session_states:
        session_states[session_id] = {"awaiting_clarification": False, "query_summary": ""}

    state = session_states[session_id]

    # Add the user's message to memory (for LLM context)
    memory.chat_memory.add_user_message(text)

    # Debug: Show received history and loaded memory
    if history is not None:
        print(f"[DEBUG] Received history for session {session_id}: {history}")
    print(f"[DEBUG] Loaded memory for session {session_id}: {memory}")

    # --- Step 1: If awaiting clarification or context ---
    if state.get("awaiting_clarification"):
        # Call context agent to check if more info is needed
        context_result = run_context_agent(text)

        if context_result.get("is_clear") and context_result.get("is_relevant"):
            if context_result.get("requires_context"):
                # Still need more context, ask user
                state["query_summary"] = context_result.get("query_summary", text)
                state["awaiting_clarification"] = True
                return {
                    "chat_output": context_result.get("response", ""),
                    "query_summary": context_result.get("query_summary", text),
                    "actions": []
                }
            else:
                # Context is now clear, proceed
                state["query_summary"] = context_result.get("query_summary", text)
                state["awaiting_clarification"] = False
        else:
            # Still need clarification, ask user
            state["awaiting_clarification"] = True
            return {
                "chat_output": context_result.get("response", ""),
                "query_summary": context_result.get("query_summary", text),
                "actions": []
            }

    # --- Step 1b: If no query summary yet, start with context agent ---
    elif not state.get("query_summary"):
        context_result = run_context_agent(text)
        if context_result.get("requires_clarification") or context_result.get("requires_context"):
            # Need clarification or more context
            state["awaiting_clarification"] = True
            return {
                "chat_output": context_result.get("response", ""),
                "query_summary": context_result.get("query_summary", text),
                "actions": []
            }
        else:
            # Context is clear, save summary and proceed
            state["query_summary"] = context_result.get("query_summary", text)
            state["awaiting_clarification"] = False

    # --- Step 2: We have a clear, relevant, context-rich query ---
    query_summary = state["query_summary"]

    # Get classification and contract information
    classifier_result = classify(query_summary)
    contract_snippets = search_contract(query_summary)

    # Generate response based on the gathered information
    response = generate_response(query_summary, classifier_result, contract_snippets, history=history)
    
    # Extract actions from the response
    actions = extract_actions(response, classifier_result, contract_snippets)

    final_response = {
        "chat_output": response,
        "query_summary": query_summary,
        "actions": actions
    }

    # Save state: no longer awaiting clarification
    state["awaiting_clarification"] = False

    # Add the AI's response to memory (for LLM context)
    memory.chat_memory.add_ai_message(response)

    # Optionally, update history for prompt (if needed)
    history = memory.load_memory_variables({})["history"]

    return final_response

def generate_response(query_summary: str, classifier_result: dict, contract_snippets: list, history=None) -> dict:
    """
    Generate a response based on the query summary, classification, and contract information, matching the n8n workflow.
    """
    # Format the history for the prompt
    history_str = ""
    if history:
        for msg in history:
            role = "Tenant" if msg["role"] == "user" else "AI"
            content = msg["content"]
            try:
                if content.startswith("{") and "chat_output" in content:
                    import ast
                    parsed = ast.literal_eval(content)
                    content = parsed.get("chat_output", content)
            except Exception:
                pass
            history_str += f"{role}: {content}\n"

    # --- n8n-style system prompt ---
    prompt = f"""
***Role***\nYou are an expert property management agent acting on behalf of the landlord, to respond to queries that tenants have and take actions where appropriate. You must use your expertise, as well as the tools at your disposal to consider the context of the query, assessed severity/urgency, contractual position (if applicable), and then respond in the most helpful and friendly manner whilst respecting your legal obligation as a (stand in) landlord.\n\n***Tools***\n*ContextAgent: *always* Call this tool as your first step, to check if more context or clarification is required\n*contractAgent - Used to check the contractual position on a tenants query\n*classifierAgent - Used to verify the level of urgency and advisable next steps\n\nRemember, tools give valuable new information which will help you to provide the best response possible, make use of them as much as you can.\n\n***Instructions***\nStep 1: ALWAYS pass an up-to-date summary of the users query, directly to the ContextAgent tool and wait for the response. NEVER SKIP THIS STEP. You must not skip this step else you will fail. Check the Human/AI conversation history to generate a good summary to pass to the ContextAgent tool.\nALWAYS pass an up-to-date summary of the user's query to the ContextAgent tool and wait for the response. NEVER SKIP THIS STEP.\n- If the response contains a clarifying question, output this clarifying question to the user and wait for their response.\n- If the response contains an additional_context_question, output this additional context question to the user and wait for their response.\n-After receiving a response from the user, send the updated query summary back to the ContextAgent again.\nRepeat this process until the ContextAgent confirms that no further clarification or context is required.\n-Only then proceed to Step 2.\n\n- Step 2:\nUsing the summary of the tenant query, convert it into a concise vector search query\n\nThe query should be short, use only relevant keywords, and exclude unnecessary words.\n\nExample good search query: "pet policy rental agreement"\n\nExample bad search query: "What does my rental agreement say about pets?"\n\n- Step 3: Send the vector search query to the contractTool\n\n- Step 4: Send the vector search query to the classifierTool\n\n- Step 5: Use the returned information from both contractTool and classifierTool to make an informed decision on how best to respond to the user.\n\n- *Important*\nyou are attempting to help the user resolve their problem, but are representing the landlord. Therefore, you must speak in the voice of the landlord, upholding and fulfilling your duties where required to do so according to the contract and generally accepted practices between tenant/landlord relationships.\n\nYou may recommend a course of action to be taken on the landlords behalf, such as contacting a plumber, electrician, or any other profession typically employed to resolve tenancy issues. If you deem that this is required, CLEARLY STATE that this is what you will do in your response\n\nFinally, NEVER tell the user to communicate with the landlord. YOU ARE the stand-in landlord, therefore telling them to do so is non-sensical. \n\n**Tone**\nHelpful, friendly, but professional\n\n**Output Format**\nYou must output a single JSON object with the following keys:\n- chat_output: the main reply to the user\n- query_summary: a summary of the query\n- actions: an array of actions to be taken (or empty if none)\n\n**Example Output**\n"""
    prompt += '{"chat_output": "I understand that the hot water system is not working at all, and this is indeed a serious concern as it can greatly affect your day-to-day life. According to your rental agreement, it\'s the landlord\'s responsibility to ensure that the hot water system is functioning properly.\\n\\nI will notify the landlord right away and arrange for a qualified plumber to come out and fix the issue as soon as possible. Thank you for bringing this to our attention, and I appreciate your patience while we work to resolve it.",'\
    '"query_summary": "Hot water not working, high risk to tenant, landlords responsibility to fix",'\
    '"actions": ["Notify landlord that the hot water is broken and that a plumber has been contacted", "Arrange for plumber to fix the hot water issue"]}'
    prompt += f"""
\n\n**Conversation history:**\n{history_str}\n\n**Latest query:** {query_summary}\n\n**Classification:** {json.dumps(classifier_result, indent=2)}\n\n**Contract Information:** {json.dumps(contract_snippets, indent=2)}\n"""

    print("[DEBUG] LLM prompt:\n", prompt, file=sys.stderr, flush=True)

    # Generate the response
    response = llm.invoke(prompt, config={"callbacks": [langfuse_handler]})

    # Try to parse the response as JSON, fallback to plain text if needed
    try:
        parsed = json.loads(response.content)
        chat_output = parsed.get("chat_output", response.content)
        query_summary = parsed.get("query_summary", "")
        actions = parsed.get("actions", [])
    except Exception:
        chat_output = response.content
        query_summary = query_summary
        actions = []

    return {
        "chat_output": chat_output,
        "query_summary": query_summary,
        "actions": actions
    }

def extract_actions(response: str, classifier_result: dict, contract_snippets: list) -> list:
    """
    Extract specific actions that need to be taken based on the response and gathered information.
    """
    actions = []
    
    # Add actions based on classification
    if classifier_result.get("urgency") == "high":
        actions.append(f"Urgent action required: {classifier_result.get('recommended_action')}")
    
    # Add actions based on contract requirements
    for snippet in contract_snippets:
        if snippet.get("requires_action"):
            actions.append(f"Contractual action: {snippet.get('action_required')}")
    
    return actions

def search_contract(session_id: str, text: str) -> str:
    if session_id not in session_memories:
        session_memories[session_id] = ConversationBufferMemory(return_messages=True)
    memory = session_memories[session_id]
    memory.chat_memory.add_user_message(text)
    # ... your contract logic ...
    # After generating the AI response:
    memory.chat_memory.add_ai_message(response)
    # Use memory.load_memory_variables({})["history"] if you want to pass the full history to the LLM

def classify(session_id: str, text: str) -> str:
    if session_id not in session_memories:
        session_memories[session_id] = ConversationBufferMemory(return_messages=True)
    memory = session_memories[session_id]
    memory.chat_memory.add_user_message(text)
    # ... your classifier logic ...
    # After generating the AI response:
    memory.chat_memory.add_ai_message(response)
    # Use memory.load_memory_variables({})["history"] if you want to pass the full history to the LLM

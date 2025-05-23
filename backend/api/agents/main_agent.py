import os, json
from langchain_openai import ChatOpenAI
from agents.context_agent import run_context_agent
from agents.classifier import classify
from agents.contract_agent import search_contract

# session_id → memory (acts like a short-term session tracker)
session_memory = {}

def handle_message(session_id: str, text: str) -> dict:
    """
    Main agent logic with memory. Handles clarification, context, and routes to tools.
    Returns a structured response with chat output, query summary, and actions.
    """
    memory = session_memory.get(session_id, {})

    # --- Step 1: If awaiting clarification or context ---
    if memory.get("awaiting_clarification"):
        context_result = run_context_agent(text)

        if context_result.get("is_clear") and context_result.get("is_relevant"):
            if context_result.get("requires_context"):
                memory["query_summary"] = context_result.get("query_summary", text)
                memory["awaiting_clarification"] = True
                session_memory[session_id] = memory
                return {
                    "chat_output": context_result.get("response", ""),
                    "query_summary": context_result.get("query_summary", text),
                    "actions": []
                }
            else:
                memory["query_summary"] = context_result.get("query_summary", text)
                memory["awaiting_clarification"] = False
                session_memory[session_id] = memory
        else:
            memory["awaiting_clarification"] = True
            session_memory[session_id] = memory
            return {
                "chat_output": context_result.get("response", ""),
                "query_summary": context_result.get("query_summary", text),
                "actions": []
            }

    elif "query_summary" not in memory:
        context_result = run_context_agent(text)

        if context_result.get("requires_clarification") or context_result.get("requires_context"):
            memory["awaiting_clarification"] = True
            session_memory[session_id] = memory
            return {
                "chat_output": context_result.get("response", ""),
                "query_summary": context_result.get("query_summary", text),
                "actions": []
            }
        else:
            memory["query_summary"] = context_result.get("query_summary", text)
            memory["awaiting_clarification"] = False
            session_memory[session_id] = memory

    # --- Step 2: We have a clear, relevant, context-rich query ---
    query_summary = memory["query_summary"]

    # Get classification and contract information
    classifier_result = classify(query_summary)
    contract_snippets = search_contract(query_summary)

    # Generate response based on the gathered information
    response = generate_response(query_summary, classifier_result, contract_snippets)
    
    # Extract actions from the response
    actions = extract_actions(response, classifier_result, contract_snippets)

    final_response = {
        "chat_output": response,
        "query_summary": query_summary,
        "actions": actions
    }

    # Save state
    memory["awaiting_clarification"] = False
    session_memory[session_id] = memory

    return final_response

def generate_response(query_summary: str, classifier_result: dict, contract_snippets: list) -> str:
    """
    Generate a response based on the query summary, classification, and contract information.
    """
    # Initialize the language model
    llm = ChatOpenAI(
        model_name="gpt-4-turbo-preview",
        temperature=0.7
    )

    # Create the prompt
    prompt = f"""
    As a property management agent representing the landlord, respond to the following tenant query:
    
    Query: {query_summary}
    
    Classification: {json.dumps(classifier_result, indent=2)}
    
    Contract Information: {json.dumps(contract_snippets, indent=2)}
    
    Provide a helpful, friendly, but professional response that:
    1. Acknowledges the tenant's concern
    2. References relevant contract information
    3. Takes appropriate action based on the classification
    4. Maintains a professional landlord-tenant relationship
    
    Remember: You are the landlord's representative, so don't tell the tenant to contact the landlord.
    """

    # Generate the response
    response = llm.invoke(prompt)
    return response.content

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

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
                return context_result
            else:
                memory["query_summary"] = context_result.get("query_summary", text)
                memory["awaiting_clarification"] = False
                session_memory[session_id] = memory  # <- Add this line
        else:
            memory["awaiting_clarification"] = True
            session_memory[session_id] = memory
            return context_result

    elif "query_summary" not in memory:
        context_result = run_context_agent(text)

        if context_result.get("requires_clarification") or context_result.get("requires_context"):
            memory["awaiting_clarification"] = True
            session_memory[session_id] = memory
            return context_result
        else:
            memory["query_summary"] = context_result.get("query_summary", text)
            memory["awaiting_clarification"] = False
            session_memory[session_id] = memory

    # --- Step 2: We have a clear, relevant, context-rich query ---
    query_summary = memory["query_summary"]

    classifier_result = classify(query_summary)
    contract_snippets = search_contract(query_summary)

    final_response = {
        "query_summary": query_summary,
        "classifier": classifier_result,
        "contract_snippets": contract_snippets
    }

    # Save state
    memory["awaiting_clarification"] = False
    session_memory[session_id] = memory

    return final_response

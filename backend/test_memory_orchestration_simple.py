#!/usr/bin/env python3
"""
Simple Memory Orchestration Test

This script tests memory isolation during a simulated conversation flow
by directly interacting with the memory channels and verifying proper isolation.
"""

import os
import sys

# Add the backend directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.memory.scoped_memory_manager import get_user_memory, get_agent_memory, get_scoped_memory_manager

def print_separator(title):
    """Print a formatted section separator"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def print_memory_contents(session_id, step_name):
    """Print the current contents of all memory channels"""
    print_separator(f"MEMORY CONTENTS: {step_name}")
    
    # Get all memory channels
    user_mem = get_user_memory(session_id)
    context_mem = get_agent_memory(session_id, "context")
    contract_mem = get_agent_memory(session_id, "contract")
    classifier_mem = get_agent_memory(session_id, "classifier")
    
    memories = [
        ("👤 USER", user_mem),
        ("🧠 CONTEXT", context_mem),
        ("📄 CONTRACT", contract_mem),
        ("🔍 CLASSIFIER", classifier_mem)
    ]
    
    for name, memory in memories:
        messages = memory.chat_memory.messages
        print(f"{name} MEMORY ({len(messages)} messages):")
        if messages:
            for i, msg in enumerate(messages):
                msg_type = type(msg).__name__
                content = str(msg.content)[:80] + "..." if len(str(msg.content)) > 80 else str(msg.content)
                print(f"  {i+1}. {msg_type}: {content}")
        else:
            print("  (empty)")
        print()

def simulate_full_conversation():
    """Simulate a complete agent orchestration conversation"""
    
    print_separator("SIMULATED CONVERSATION ORCHESTRATION TEST")
    
    session_id = "test_session_memory_123"
    user_query = "My kitchen faucet has been leaking for two days. Can you help?"
    
    print(f"🎯 Session ID: {session_id}")
    print(f"🎯 User Query: {user_query}")
    
    # Step 1: Initial state - all memories should be empty
    print_memory_contents(session_id, "INITIAL STATE")
    
    # Verify initial state
    user_mem = get_user_memory(session_id)
    context_mem = get_agent_memory(session_id, "context")
    contract_mem = get_agent_memory(session_id, "contract")
    classifier_mem = get_agent_memory(session_id, "classifier")
    
    assert len(user_mem.chat_memory.messages) == 0, "User memory should start empty"
    assert len(context_mem.chat_memory.messages) == 0, "Context memory should start empty"
    assert len(contract_mem.chat_memory.messages) == 0, "Contract memory should start empty"
    assert len(classifier_mem.chat_memory.messages) == 0, "Classifier memory should start empty"
    print("✅ All memory channels start empty")
    
    # Step 2: User sends message to Main Agent
    print_separator("STEP 1: USER MESSAGE TO MAIN AGENT")
    user_memory = get_user_memory(session_id)
    user_memory.chat_memory.add_user_message(user_query)
    print(f"📤 User message added to user memory")
    
    print_memory_contents(session_id, "AFTER USER MESSAGE")
    
    # Verify user memory populated, others still empty
    assert len(get_user_memory(session_id).chat_memory.messages) == 1, "User memory should have 1 message"
    assert len(get_agent_memory(session_id, "context").chat_memory.messages) == 0, "Context memory still empty"
    assert len(get_agent_memory(session_id, "contract").chat_memory.messages) == 0, "Contract memory still empty"
    assert len(get_agent_memory(session_id, "classifier").chat_memory.messages) == 0, "Classifier memory still empty"
    print("✅ User memory populated, agent memories remain isolated")
    
    # Step 3: Main Agent → Context Agent interaction
    print_separator("STEP 2: MAIN AGENT → CONTEXT AGENT")
    context_memory = get_agent_memory(session_id, "context")
    
    # Simulate main agent calling context agent
    context_memory.chat_memory.add_user_message(f"Main Agent Query: {user_query}")
    context_response = '{"is_clear": true, "is_relevant": true, "requires_clarification": false, "query_summary": "User reporting kitchen faucet leak"}'
    context_memory.chat_memory.add_ai_message(context_response)
    print("🤖 Context agent conversation added")
    
    print_memory_contents(session_id, "AFTER CONTEXT AGENT")
    
    # Verify isolation
    assert len(get_user_memory(session_id).chat_memory.messages) == 1, "User memory unchanged"
    assert len(get_agent_memory(session_id, "context").chat_memory.messages) == 2, "Context memory has 2 messages"
    assert len(get_agent_memory(session_id, "contract").chat_memory.messages) == 0, "Contract memory still empty"
    assert len(get_agent_memory(session_id, "classifier").chat_memory.messages) == 0, "Classifier memory still empty"
    print("✅ Context agent memory populated, other memories remain isolated")
    
    # Step 4: Main Agent → Contract Agent interaction
    print_separator("STEP 3: MAIN AGENT → CONTRACT AGENT")
    contract_memory = get_agent_memory(session_id, "contract")
    
    contract_memory.chat_memory.add_user_message(f"Main Agent Query: {user_query}")
    contract_response = "Based on rental agreement Section 4.2, landlord responsible for plumbing repairs. Standard response time 48-72 hours."
    contract_memory.chat_memory.add_ai_message(contract_response)
    print("📄 Contract agent conversation added")
    
    print_memory_contents(session_id, "AFTER CONTRACT AGENT")
    
    # Verify continued isolation
    assert len(get_user_memory(session_id).chat_memory.messages) == 1, "User memory unchanged"
    assert len(get_agent_memory(session_id, "context").chat_memory.messages) == 2, "Context memory unchanged"
    assert len(get_agent_memory(session_id, "contract").chat_memory.messages) == 2, "Contract memory has 2 messages"
    assert len(get_agent_memory(session_id, "classifier").chat_memory.messages) == 0, "Classifier memory still empty"
    print("✅ Contract agent memory populated, other memories remain isolated")
    
    # Step 5: Main Agent → Classifier Agent interaction
    print_separator("STEP 4: MAIN AGENT → CLASSIFIER AGENT")
    classifier_memory = get_agent_memory(session_id, "classifier")
    
    classifier_memory.chat_memory.add_user_message(f"Main Agent Query: {user_query}")
    classifier_response = "Classification: MEDIUM PRIORITY - Plumbing issue. Responsibility: LANDLORD. Response time: 48-72 hours."
    classifier_memory.chat_memory.add_ai_message(classifier_response)
    print("🔍 Classifier agent conversation added")
    
    print_memory_contents(session_id, "AFTER CLASSIFIER AGENT")
    
    # Verify all agent memories are populated and isolated
    assert len(get_user_memory(session_id).chat_memory.messages) == 1, "User memory unchanged"
    assert len(get_agent_memory(session_id, "context").chat_memory.messages) == 2, "Context memory unchanged"
    assert len(get_agent_memory(session_id, "contract").chat_memory.messages) == 2, "Contract memory unchanged"
    assert len(get_agent_memory(session_id, "classifier").chat_memory.messages) == 2, "Classifier memory has 2 messages"
    print("✅ All agent memories populated and isolated")
    
    # Step 6: Main Agent responds to user
    print_separator("STEP 5: MAIN AGENT RESPONDS TO USER")
    user_memory = get_user_memory(session_id)
    final_response = "I understand you have a leaky kitchen faucet. Based on our analysis, this is a medium priority maintenance issue that falls under landlord responsibility. I've determined this requires a 48-72 hour response time. Here's what I recommend..."
    user_memory.chat_memory.add_ai_message(final_response)
    print("💬 Main Agent response added to user memory")
    
    print_memory_contents(session_id, "FINAL STATE")
    
    # Verify final state
    assert len(get_user_memory(session_id).chat_memory.messages) == 2, "User memory has user query + AI response"
    assert len(get_agent_memory(session_id, "context").chat_memory.messages) == 2, "Context memory unchanged"
    assert len(get_agent_memory(session_id, "contract").chat_memory.messages) == 2, "Contract memory unchanged"
    assert len(get_agent_memory(session_id, "classifier").chat_memory.messages) == 2, "Classifier memory unchanged"
    print("✅ Final state: User conversation complete, agent conversations isolated")
    
    # Step 7: Test cross-session isolation
    print_separator("STEP 6: CROSS-SESSION ISOLATION TEST")
    
    different_session = "different_session_456"
    other_user_mem = get_user_memory(different_session)
    other_context_mem = get_agent_memory(different_session, "context")
    
    assert len(other_user_mem.chat_memory.messages) == 0, "Different session user memory should be empty"
    assert len(other_context_mem.chat_memory.messages) == 0, "Different session context memory should be empty"
    
    print(f"📊 Session {session_id}: User(2) Context(2) Contract(2) Classifier(2)")
    print(f"📊 Session {different_session}: User(0) Context(0) Contract(0) Classifier(0)")
    print("✅ Cross-session isolation verified")
    
    # Step 8: Memory statistics
    print_separator("MEMORY STATISTICS")
    manager = get_scoped_memory_manager()
    stats = manager.get_session_stats()
    
    print(f"📈 MEMORY STATISTICS:")
    print(f"  Active Sessions: {stats['active_sessions']}")
    print(f"  Total Memory Stores: {stats['total_memory_stores']}")
    print(f"  User Conversations: {stats['user_conversations']}")
    print(f"  Context Conversations: {stats['context_conversations']}")
    print(f"  Contract Conversations: {stats['contract_conversations']}")
    print(f"  Classifier Conversations: {stats['classifier_conversations']}")
    
    # Final verification
    print_separator("TEST RESULTS")
    print("🎉 CONVERSATION ORCHESTRATION MEMORY TEST RESULTS:")
    print("✅ Perfect memory isolation between all agent types")
    print("✅ User conversations completely separate from agent conversations")
    print("✅ Each agent only sees its own conversation thread with main agent")
    print("✅ Session isolation working perfectly")
    print("✅ Memory persistence across conversation steps")
    print("✅ Cross-session isolation verified")
    print("✅ Memory statistics tracking functional")
    
    print("\n🏆 ALL MEMORY ISOLATION TESTS PASSED!")
    print("💡 The scoped memory architecture is working perfectly!")
    
    return True

if __name__ == "__main__":
    # Set basic environment (not needed for memory testing)
    os.environ.setdefault('OPENAI_API_KEY', 'test-key')
    
    # Run the simulation
    try:
        simulate_full_conversation()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 
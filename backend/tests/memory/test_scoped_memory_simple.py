#!/usr/bin/env python3
"""
Simple test script to verify scoped memory implementation

This script tests the core functionality without requiring pytest,
making it easy to run quick verification tests.
"""

import sys
import os

# Add the current directory to Python path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_memory_isolation():
    """Test basic memory isolation between agents"""
    print("🧪 Testing basic memory isolation...")
    
    from api.memory.scoped_memory_manager import get_scoped_memory_manager
    
    manager = get_scoped_memory_manager()
    session_id = "test_basic_isolation"
    
    # Get memory for different agents
    user_memory = manager.get_user_memory(session_id)
    context_memory = manager.get_agent_memory(session_id, "context")
    contract_memory = manager.get_agent_memory(session_id, "contract")
    classifier_memory = manager.get_agent_memory(session_id, "classifier")
    
    # Verify they are different objects
    assert user_memory is not context_memory, "User and context memory should be different"
    assert context_memory is not contract_memory, "Context and contract memory should be different"
    assert contract_memory is not classifier_memory, "Contract and classifier memory should be different"
    
    print("✅ Memory objects are properly isolated")
    
    # Test conversation isolation
    user_memory.chat_memory.add_user_message("User says hello")
    context_memory.chat_memory.add_user_message("Context agent query")
    
    # Check that context agent doesn't see user conversation
    context_vars = context_memory.load_memory_variables({})
    context_history = context_vars.get("chat_history", [])
    
    user_vars = user_memory.load_memory_variables({})
    user_history = user_vars.get("chat_history", [])
    
    assert len(context_history) == 1, f"Context should have 1 message, got {len(context_history)}"
    assert len(user_history) == 1, f"User should have 1 message, got {len(user_history)}"
    
    # Verify content isolation
    context_content = str(context_history[0])
    user_content = str(user_history[0])
    
    assert "Context agent query" in context_content, "Context memory should contain context query"
    assert "User says hello" not in context_content, "Context memory should not contain user message"
    assert "User says hello" in user_content, "User memory should contain user message"
    assert "Context agent query" not in user_content, "User memory should not contain context query"
    
    print("✅ Conversation content is properly isolated")
    return True


def test_agent_memory_functions():
    """Test that agent memory functions work correctly"""
    print("🧪 Testing agent memory functions...")
    
    from api.agents.context_agent import get_shared_memory as get_context_memory
    from api.agents.contract_agent import get_shared_memory as get_contract_memory
    from api.agents.classifier import get_shared_memory as get_classifier_memory
    from api.agents.main_agent import get_shared_memory as get_user_memory
    
    session_id = "test_agent_functions"
    
    # Get memory through agent functions
    user_mem = get_user_memory(session_id)
    context_mem = get_context_memory(session_id)
    contract_mem = get_contract_memory(session_id)
    classifier_mem = get_classifier_memory(session_id)
    
    # Verify isolation
    assert user_mem is not context_mem, "User and context memory should be different"
    assert context_mem is not contract_mem, "Context and contract memory should be different"
    assert contract_mem is not classifier_mem, "Contract and classifier memory should be different"
    
    # Verify proper types
    from langchain.memory import ConversationBufferWindowMemory
    assert isinstance(user_mem, ConversationBufferWindowMemory), "Should return ConversationBufferWindowMemory"
    assert isinstance(context_mem, ConversationBufferWindowMemory), "Should return ConversationBufferWindowMemory"
    
    # Verify window sizes
    assert user_mem.k == 10, f"User memory should have window size 10, got {user_mem.k}"
    assert context_mem.k == 5, f"Context memory should have window size 5, got {context_mem.k}"
    
    print("✅ Agent memory functions work correctly")
    return True


def test_session_isolation():
    """Test that different sessions are isolated"""
    print("🧪 Testing session isolation...")
    
    from api.memory.scoped_memory_manager import get_scoped_memory_manager
    
    manager = get_scoped_memory_manager()
    
    session_1 = "test_session_1"
    session_2 = "test_session_2"
    
    # Get memories for different sessions
    user_mem_1 = manager.get_user_memory(session_1)
    user_mem_2 = manager.get_user_memory(session_2)
    
    context_mem_1 = manager.get_agent_memory(session_1, "context")
    context_mem_2 = manager.get_agent_memory(session_2, "context")
    
    # Verify they are different objects
    assert user_mem_1 is not user_mem_2, "Different sessions should have different user memories"
    assert context_mem_1 is not context_mem_2, "Different sessions should have different context memories"
    
    # Add conversation to session 1
    user_mem_1.chat_memory.add_user_message("Session 1 message")
    context_mem_1.chat_memory.add_user_message("Session 1 context")
    
    # Verify session 2 doesn't see session 1 conversations
    user_vars_2 = user_mem_2.load_memory_variables({})
    context_vars_2 = context_mem_2.load_memory_variables({})
    
    assert len(user_vars_2.get("chat_history", [])) == 0, "Session 2 should not see session 1 user conversation"
    assert len(context_vars_2.get("chat_history", [])) == 0, "Session 2 should not see session 1 context conversation"
    
    print("✅ Session isolation works correctly")
    return True


def test_memory_statistics():
    """Test memory statistics functionality"""
    print("🧪 Testing memory statistics...")
    
    from api.memory.scoped_memory_manager import get_scoped_memory_manager
    
    manager = get_scoped_memory_manager()
    
    # Reset by creating a new manager
    from api.memory.scoped_memory_manager import ScopedMemoryManager
    fresh_manager = ScopedMemoryManager()
    
    # Initially empty
    stats = fresh_manager.get_session_stats()
    assert stats["active_sessions"] == 0, "Should start with 0 active sessions"
    assert stats["total_memory_stores"] == 0, "Should start with 0 memory stores"
    
    # Add some memories
    fresh_manager.get_user_memory("session_stats_1")
    fresh_manager.get_agent_memory("session_stats_1", "context")
    fresh_manager.get_agent_memory("session_stats_2", "contract")
    
    # Check updated stats
    stats = fresh_manager.get_session_stats()
    assert stats["active_sessions"] == 2, f"Should have 2 active sessions, got {stats['active_sessions']}"
    assert stats["user_conversations"] == 1, f"Should have 1 user conversation, got {stats['user_conversations']}"
    assert stats["context_conversations"] == 1, f"Should have 1 context conversation, got {stats['context_conversations']}"
    assert stats["contract_conversations"] == 1, f"Should have 1 contract conversation, got {stats['contract_conversations']}"
    assert stats["classifier_conversations"] == 0, f"Should have 0 classifier conversations, got {stats['classifier_conversations']}"
    assert stats["total_memory_stores"] == 3, f"Should have 3 total memory stores, got {stats['total_memory_stores']}"
    
    print("✅ Memory statistics work correctly")
    return True


def test_n8n_conversation_scoping():
    """Test that conversation scoping matches n8n architecture"""
    print("🧪 Testing n8n conversation scoping...")
    
    from api.memory.scoped_memory_manager import get_scoped_memory_manager
    
    manager = get_scoped_memory_manager()
    session_id = "test_n8n_scoping"
    
    # Get all memory channels
    user_memory = manager.get_user_memory(session_id)
    context_memory = manager.get_agent_memory(session_id, "context")
    contract_memory = manager.get_agent_memory(session_id, "contract")
    classifier_memory = manager.get_agent_memory(session_id, "classifier")
    
    # Simulate n8n conversation flow
    
    # 1. User talks to main agent
    user_memory.chat_memory.add_user_message("My washing machine is broken")
    user_memory.chat_memory.add_ai_message("I'll help you with that issue")
    
    # 2. Main agent talks to context agent
    context_memory.chat_memory.add_user_message("washing machine broken")
    context_memory.chat_memory.add_ai_message("Need more details - which room, when did it start?")
    
    # 3. Main agent talks to contract agent
    contract_memory.chat_memory.add_user_message("appliance repair responsibility")
    contract_memory.chat_memory.add_ai_message("Landlord responsible for major appliances")
    
    # 4. Main agent talks to classifier agent
    classifier_memory.chat_memory.add_user_message("broken washing machine")
    classifier_memory.chat_memory.add_ai_message("Medium priority - appliance repair, 48hr response")
    
    # Verify each agent only sees its own conversation thread
    context_vars = context_memory.load_memory_variables({})
    contract_vars = contract_memory.load_memory_variables({})
    classifier_vars = classifier_memory.load_memory_variables({})
    user_vars = user_memory.load_memory_variables({})
    
    # Each should have exactly 2 messages (1 exchange)
    assert len(context_vars.get("chat_history", [])) == 2, f"Context should have 2 messages, got {len(context_vars.get('chat_history', []))}"
    assert len(contract_vars.get("chat_history", [])) == 2, f"Contract should have 2 messages, got {len(contract_vars.get('chat_history', []))}"
    assert len(classifier_vars.get("chat_history", [])) == 2, f"Classifier should have 2 messages, got {len(classifier_vars.get('chat_history', []))}"
    assert len(user_vars.get("chat_history", [])) == 2, f"User should have 2 messages, got {len(user_vars.get('chat_history', []))}"
    
    # Verify content isolation
    context_content = " ".join(str(msg) for msg in context_vars.get("chat_history", []))
    contract_content = " ".join(str(msg) for msg in contract_vars.get("chat_history", []))
    classifier_content = " ".join(str(msg) for msg in classifier_vars.get("chat_history", []))
    user_content = " ".join(str(msg) for msg in user_vars.get("chat_history", []))
    
    # Context agent should only see its conversation
    assert "washing machine broken" in context_content, "Context should see its query"
    assert "Need more details" in context_content, "Context should see its response"
    assert "appliance repair responsibility" not in context_content, "Context should not see contract query"
    assert "My washing machine is broken" not in context_content, "Context should not see user message"
    
    # Contract agent should only see its conversation
    assert "appliance repair responsibility" in contract_content, "Contract should see its query"
    assert "Landlord responsible" in contract_content, "Contract should see its response"
    assert "washing machine broken" not in contract_content, "Contract should not see context query"
    assert "broken washing machine" not in contract_content, "Contract should not see classifier query"
    
    # User should only see user ↔ main agent conversation
    assert "My washing machine is broken" in user_content, "User should see user message"
    assert "I'll help you with that issue" in user_content, "User should see main agent response"
    assert "washing machine broken" not in user_content, "User should not see context query"
    assert "appliance repair responsibility" not in user_content, "User should not see contract query"
    
    print("✅ n8n conversation scoping works correctly")
    return True


def main():
    """Run all tests"""
    print("🚀 Starting Scoped Memory Manager Tests\n")
    
    tests = [
        test_basic_memory_isolation,
        test_agent_memory_functions,
        test_session_isolation,
        test_memory_statistics,
        test_n8n_conversation_scoping
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
                print(f"❌ {test.__name__} failed")
        except Exception as e:
            failed += 1
            print(f"❌ {test.__name__} failed with error: {e}")
            import traceback
            traceback.print_exc()
        print()
    
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Scoped memory implementation is working correctly.")
        return True
    else:
        print("💥 Some tests failed. Check the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 
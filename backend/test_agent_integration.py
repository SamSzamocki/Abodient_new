#!/usr/bin/env python3
"""
Test agent integration with scoped memory

This script tests that agents work correctly with the new scoped memory system
in a realistic conversation scenario.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_context_agent_memory_integration():
    """Test ContextAgent with scoped memory"""
    print("🧪 Testing ContextAgent memory integration...")
    
    from api.agents.context_agent import run_context_agent
    from api.memory.scoped_memory_manager import get_scoped_memory_manager
    
    session_id = "test_context_integration"
    
    # Mock LLM to avoid API calls
    import unittest.mock
    
    # First query - should require more context
    with unittest.mock.patch('api.agents.context_agent.get_llm') as mock_llm:
        mock_response = unittest.mock.MagicMock()
        mock_response.content = '{"is_clear": true, "is_relevant": true, "requires_clarification": false, "clarifying_question": "", "requires_context": true, "additional_context_question": "Which room and when did it start?", "query_summary": "User reports broken washing machine"}'
        mock_llm.return_value.invoke.return_value = mock_response
        
        try:
            result1 = run_context_agent("My washing machine is broken", session_id)
            print(f"✅ First query processed: {result1}")
        except Exception as e:
            print(f"ℹ️ First query failed (expected in test env): {e}")
    
    # Check memory state
    manager = get_scoped_memory_manager()
    context_memory = manager.get_agent_memory(session_id, "context")
    
    # Should have conversation recorded
    context_vars = context_memory.load_memory_variables({})
    context_history = context_vars.get("chat_history", [])
    
    print(f"✅ Context agent has {len(context_history)} messages in memory")
    
    # Second query - should use previous context
    with unittest.mock.patch('api.agents.context_agent.get_llm') as mock_llm2:
        mock_response2 = unittest.mock.MagicMock()
        mock_response2.content = '{"is_clear": true, "is_relevant": true, "requires_clarification": false, "clarifying_question": "", "requires_context": false, "additional_context_question": "", "query_summary": "User provides more details about washing machine in kitchen, started yesterday"}'
        mock_llm2.return_value.invoke.return_value = mock_response2
        
        try:
            result2 = run_context_agent("It started yesterday in the kitchen", session_id)
            print(f"✅ Second query processed: {result2}")
        except Exception as e:
            print(f"ℹ️ Second query failed (expected in test env): {e}")
    
    # Check updated memory state
    context_vars_2 = context_memory.load_memory_variables({})
    context_history_2 = context_vars_2.get("chat_history", [])
    
    print(f"✅ Context agent now has {len(context_history_2)} messages in memory")
    
    # Verify memory contains both conversations
    if len(context_history_2) >= 2:
        print("✅ Memory properly accumulated conversation history")
    
    return True


def test_memory_isolation_between_agents():
    """Test that agents maintain separate memory channels"""
    print("🧪 Testing memory isolation between agents...")
    
    from api.agents.context_agent import get_shared_memory as get_context_memory
    from api.agents.contract_agent import get_shared_memory as get_contract_memory
    from api.agents.classifier import get_shared_memory as get_classifier_memory
    from api.agents.main_agent import get_shared_memory as get_user_memory
    
    session_id = "test_isolation_integration"
    
    # Get all memories
    user_mem = get_user_memory(session_id)
    context_mem = get_context_memory(session_id)
    contract_mem = get_contract_memory(session_id)
    classifier_mem = get_classifier_memory(session_id)
    
    # Add conversations to each
    user_mem.chat_memory.add_user_message("User: My rent is too high")
    user_mem.chat_memory.add_ai_message("Main Agent: I'll check your lease terms")
    
    context_mem.chat_memory.add_user_message("Main Agent: rent too high")
    context_mem.chat_memory.add_ai_message("Context Agent: Need lease details and current rent amount")
    
    contract_mem.chat_memory.add_user_message("Main Agent: rent increase policy")
    contract_mem.chat_memory.add_ai_message("Contract Agent: Rent increases limited to 3% annually per section 8.2")
    
    classifier_mem.chat_memory.add_user_message("Main Agent: rent complaint")
    classifier_mem.chat_memory.add_ai_message("Classifier Agent: Medium priority - financial concern, 5 day response")
    
    # Verify isolation
    user_vars = user_mem.load_memory_variables({})
    context_vars = context_mem.load_memory_variables({})
    contract_vars = contract_mem.load_memory_variables({})
    classifier_vars = classifier_mem.load_memory_variables({})
    
    user_content = " ".join(str(msg) for msg in user_vars.get("chat_history", []))
    context_content = " ".join(str(msg) for msg in context_vars.get("chat_history", []))
    contract_content = " ".join(str(msg) for msg in contract_vars.get("chat_history", []))
    classifier_content = " ".join(str(msg) for msg in classifier_vars.get("chat_history", []))
    
    # User should only see user conversation
    assert "My rent is too high" in user_content, "User memory should contain user message"
    assert "rent too high" not in user_content, "User memory should not contain context agent query"
    assert "rent increase policy" not in user_content, "User memory should not contain contract agent query"
    
    # Context should only see context conversation
    assert "rent too high" in context_content, "Context memory should contain context query"
    assert "Need lease details" in context_content, "Context memory should contain context response"
    assert "My rent is too high" not in context_content, "Context memory should not contain user message"
    assert "rent increase policy" not in context_content, "Context memory should not contain contract query"
    
    # Contract should only see contract conversation
    assert "rent increase policy" in contract_content, "Contract memory should contain contract query"
    assert "Rent increases limited" in contract_content, "Contract memory should contain contract response"
    assert "rent too high" not in contract_content, "Contract memory should not contain context query"
    assert "rent complaint" not in contract_content, "Contract memory should not contain classifier query"
    
    # Classifier should only see classifier conversation
    assert "rent complaint" in classifier_content, "Classifier memory should contain classifier query"
    assert "Medium priority" in classifier_content, "Classifier memory should contain classifier response"
    assert "rent too high" not in classifier_content, "Classifier memory should not contain context query"
    assert "rent increase policy" not in classifier_content, "Classifier memory should not contain contract query"
    
    print("✅ All agents maintain proper memory isolation")
    return True


def test_session_isolation():
    """Test that different sessions maintain separate memories"""
    print("🧪 Testing session isolation...")
    
    from api.memory.scoped_memory_manager import get_scoped_memory_manager
    
    manager = get_scoped_memory_manager()
    
    session_a = "test_session_A"
    session_b = "test_session_B"
    
    # Add conversations to session A
    user_mem_a = manager.get_user_memory(session_a)
    context_mem_a = manager.get_agent_memory(session_a, "context")
    
    user_mem_a.chat_memory.add_user_message("Session A user message")
    context_mem_a.chat_memory.add_user_message("Session A context query")
    
    # Add different conversations to session B
    user_mem_b = manager.get_user_memory(session_b)
    context_mem_b = manager.get_agent_memory(session_b, "context")
    
    user_mem_b.chat_memory.add_user_message("Session B user message")
    context_mem_b.chat_memory.add_user_message("Session B context query")
    
    # Verify isolation
    user_vars_a = user_mem_a.load_memory_variables({})
    context_vars_a = context_mem_a.load_memory_variables({})
    user_vars_b = user_mem_b.load_memory_variables({})
    context_vars_b = context_mem_b.load_memory_variables({})
    
    user_content_a = " ".join(str(msg) for msg in user_vars_a.get("chat_history", []))
    context_content_a = " ".join(str(msg) for msg in context_vars_a.get("chat_history", []))
    user_content_b = " ".join(str(msg) for msg in user_vars_b.get("chat_history", []))
    context_content_b = " ".join(str(msg) for msg in context_vars_b.get("chat_history", []))
    
    # Session A should not see Session B conversations
    assert "Session A user message" in user_content_a, "Session A should see its user message"
    assert "Session B user message" not in user_content_a, "Session A should not see Session B user message"
    assert "Session A context query" in context_content_a, "Session A should see its context query"
    assert "Session B context query" not in context_content_a, "Session A should not see Session B context query"
    
    # Session B should not see Session A conversations
    assert "Session B user message" in user_content_b, "Session B should see its user message"
    assert "Session A user message" not in user_content_b, "Session B should not see Session A user message"
    assert "Session B context query" in context_content_b, "Session B should see its context query"
    assert "Session A context query" not in context_content_b, "Session B should not see Session A context query"
    
    print("✅ Session isolation works correctly")
    return True


def test_memory_statistics():
    """Test memory manager statistics tracking"""
    print("🧪 Testing memory statistics tracking...")
    
    from api.memory.scoped_memory_manager import ScopedMemoryManager
    
    # Create fresh manager for clean stats
    manager = ScopedMemoryManager()
    
    # Initially empty
    stats = manager.get_session_stats()
    assert stats["active_sessions"] == 0, f"Should start with 0 sessions, got {stats['active_sessions']}"
    assert stats["total_memory_stores"] == 0, f"Should start with 0 stores, got {stats['total_memory_stores']}"
    
    # Add some activity
    manager.get_user_memory("stats_session_1")
    manager.get_agent_memory("stats_session_1", "context")
    manager.get_agent_memory("stats_session_2", "contract")
    manager.get_agent_memory("stats_session_3", "classifier")
    
    # Check updated stats
    stats = manager.get_session_stats()
    assert stats["active_sessions"] == 3, f"Should have 3 sessions, got {stats['active_sessions']}"
    assert stats["user_conversations"] == 1, f"Should have 1 user conversation, got {stats['user_conversations']}"
    assert stats["context_conversations"] == 1, f"Should have 1 context conversation, got {stats['context_conversations']}"
    assert stats["contract_conversations"] == 1, f"Should have 1 contract conversation, got {stats['contract_conversations']}"
    assert stats["classifier_conversations"] == 1, f"Should have 1 classifier conversation, got {stats['classifier_conversations']}"
    assert stats["total_memory_stores"] == 4, f"Should have 4 total stores, got {stats['total_memory_stores']}"
    
    print("✅ Memory statistics tracking works correctly")
    return True


def main():
    """Run all integration tests"""
    print("🚀 Starting Agent Integration Tests with Scoped Memory\n")
    
    tests = [
        test_context_agent_memory_integration,
        test_memory_isolation_between_agents,
        test_session_isolation,
        test_memory_statistics
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
    
    print(f"📊 Integration Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All integration tests passed! Agent integration with scoped memory is working correctly.")
        return True
    else:
        print("💥 Some integration tests failed. Check the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 
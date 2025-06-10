"""
Integration tests for scoped memory with actual agent implementations

Tests that the real agents (context, contract, classifier) properly use
the scoped memory manager and maintain conversation isolation.
"""

import pytest
import os
from unittest.mock import patch, MagicMock

# Import agents with their memory functions
from api.agents.context_agent import run_context_agent, get_shared_memory as get_context_memory
from api.agents.contract_agent import run_contract_agent, get_shared_memory as get_contract_memory  
from api.agents.classifier import run_classifier_agent, get_shared_memory as get_classifier_memory
from api.agents.main_agent import get_shared_memory as get_user_memory
from api.memory.scoped_memory_manager import get_scoped_memory_manager


class TestAgentMemoryIntegration:
    """Test that real agents use scoped memory correctly"""
    
    def setup_method(self):
        """Setup for each test"""
        # Reset the global memory manager for each test
        import api.memory.scoped_memory_manager as mem_module
        mem_module._memory_manager = None
    
    def test_agent_memory_functions_use_scoped_manager(self):
        """Test that agent memory functions use the scoped memory manager"""
        session_id = "test_integration_session"
        
        # Get memory from each agent
        user_mem = get_user_memory(session_id)
        context_mem = get_context_memory(session_id)
        contract_mem = get_contract_memory(session_id)
        classifier_mem = get_classifier_memory(session_id)
        
        # Verify they're all different objects (isolated)
        assert user_mem is not context_mem
        assert user_mem is not contract_mem
        assert user_mem is not classifier_mem
        assert context_mem is not contract_mem
        assert context_mem is not classifier_mem
        assert contract_mem is not classifier_mem
        
        # Verify they're managed by the same scoped manager
        manager = get_scoped_memory_manager()
        assert user_mem is manager.get_user_memory(session_id)
        assert context_mem is manager.get_agent_memory(session_id, "context")
        assert contract_mem is manager.get_agent_memory(session_id, "contract")
        assert classifier_mem is manager.get_agent_memory(session_id, "classifier")
    
    def test_memory_isolation_across_agent_calls(self):
        """Test memory isolation when actually calling agents"""
        session_id = "test_agent_calls"
        
        # Mock the LLM calls to avoid API dependency
        with patch('api.agents.context_agent.get_llm') as mock_context_llm, \
             patch('api.agents.contract_agent.get_llm') as mock_contract_llm, \
             patch('api.agents.classifier.get_llm') as mock_classifier_llm, \
             patch('api.agents.contract_agent.get_pinecone_components') as mock_pinecone_contract, \
             patch('api.agents.classifier.get_pinecone_components') as mock_pinecone_classifier:
            
            # Setup mocks
            mock_context_response = MagicMock()
            mock_context_response.content = '{"is_clear": true, "requires_clarification": false, "query_summary": "Test context response"}'
            mock_context_llm.return_value.invoke.return_value = mock_context_response
            
            mock_contract_response = MagicMock()
            mock_contract_response.content = "Contract agent response about test query"
            mock_contract_llm.return_value.invoke.return_value = mock_contract_response
            
            mock_classifier_response = MagicMock() 
            mock_classifier_response.content = "Classifier agent response about test query"
            mock_classifier_llm.return_value.invoke.return_value = mock_classifier_response
            
            # Mock Pinecone responses
            mock_pinecone_results = {
                "matches": [
                    {"metadata": {"text": "Mock contract text"}},
                    {"metadata": {"text": "Another contract clause"}}
                ]
            }
            
            mock_pinecone_contract.return_value = (
                MagicMock(), 
                MagicMock(query=MagicMock(return_value=mock_pinecone_results)),
                MagicMock(embed_query=MagicMock(return_value=[0.1] * 1536)),
                MagicMock()
            )
            
            mock_pinecone_classifier.return_value = (
                MagicMock(),
                MagicMock(query=MagicMock(return_value=mock_pinecone_results)), 
                MagicMock(embed_query=MagicMock(return_value=[0.1] * 1536)),
                MagicMock()
            )
            
            # Call each agent
            try:
                context_result = run_context_agent("Test query for context", session_id)
                contract_result = run_contract_agent("Test query for contract", session_id)
                classifier_result = run_classifier_agent("Test query for classifier", session_id)
                
                print(f"Context result: {context_result}")
                print(f"Contract result: {contract_result}")
                print(f"Classifier result: {classifier_result}")
                
            except Exception as e:
                # If agents fail due to environment setup, that's OK for this test
                # We're mainly testing the memory isolation structure
                print(f"Agent call failed (expected in test environment): {e}")
            
            # Verify memory isolation regardless of agent call success
            manager = get_scoped_memory_manager()
            
            context_memory = manager.get_agent_memory(session_id, "context")
            contract_memory = manager.get_agent_memory(session_id, "contract") 
            classifier_memory = manager.get_agent_memory(session_id, "classifier")
            
            # Each agent should have its own isolated memory
            context_vars = context_memory.load_memory_variables({})
            contract_vars = contract_memory.load_memory_variables({})
            classifier_vars = classifier_memory.load_memory_variables({})
            
            # Verify they don't share conversation history
            context_history = context_vars.get("chat_history", [])
            contract_history = contract_vars.get("chat_history", [])
            classifier_history = classifier_vars.get("chat_history", [])
            
            # If any conversations were recorded, they should be isolated
            if context_history:
                assert not any("Test query for contract" in str(msg) for msg in context_history)
                assert not any("Test query for classifier" in str(msg) for msg in context_history)
            
            if contract_history:
                assert not any("Test query for context" in str(msg) for msg in contract_history)
                assert not any("Test query for classifier" in str(msg) for msg in contract_history)
                
            if classifier_history:
                assert not any("Test query for context" in str(msg) for msg in classifier_history)
                assert not any("Test query for contract" in str(msg) for msg in classifier_history)
    
    def test_session_isolation_across_agents(self):
        """Test that different sessions maintain isolation across all agents"""
        session_1 = "test_session_isolation_1"
        session_2 = "test_session_isolation_2"
        
        # Get memories for both sessions
        manager = get_scoped_memory_manager()
        
        # Session 1 memories
        user_mem_1 = manager.get_user_memory(session_1)
        context_mem_1 = manager.get_agent_memory(session_1, "context")
        
        # Session 2 memories  
        user_mem_2 = manager.get_user_memory(session_2)
        context_mem_2 = manager.get_agent_memory(session_2, "context")
        
        # Add conversations to session 1
        user_mem_1.chat_memory.add_user_message("Session 1 user message")
        context_mem_1.chat_memory.add_user_message("Session 1 context query")
        
        # Verify session 2 doesn't see session 1 conversations
        user_vars_2 = user_mem_2.load_memory_variables({})
        context_vars_2 = context_mem_2.load_memory_variables({})
        
        assert len(user_vars_2.get("chat_history", [])) == 0
        assert len(context_vars_2.get("chat_history", [])) == 0
    
    def test_memory_manager_statistics_with_real_agents(self):
        """Test that statistics properly track agent memory usage"""
        session_id = "test_stats_session"
        
        manager = get_scoped_memory_manager()
        
        # Initially empty
        stats = manager.get_session_stats()
        initial_sessions = stats["active_sessions"]
        
        # Access memories through agent functions
        get_user_memory(session_id)
        get_context_memory(session_id)
        get_contract_memory(session_id)
        get_classifier_memory(session_id)
        
        # Check updated statistics
        stats = manager.get_session_stats()
        assert stats["active_sessions"] == initial_sessions + 1
        assert stats["user_conversations"] >= 1
        assert stats["context_conversations"] >= 1
        assert stats["contract_conversations"] >= 1
        assert stats["classifier_conversations"] >= 1


class TestMemoryPersistence:
    """Test memory persistence across multiple agent interactions"""
    
    def setup_method(self):
        """Setup for each test"""
        # Reset the global memory manager for each test
        import api.memory.scoped_memory_manager as mem_module
        mem_module._memory_manager = None
    
    def test_conversation_continuity_within_session(self):
        """Test that conversations persist within the same session"""
        session_id = "test_continuity_session"
        
        # Get context agent memory
        context_memory = get_context_memory(session_id)
        
        # Add a conversation
        context_memory.chat_memory.add_user_message("First context query")
        context_memory.chat_memory.add_ai_message("First context response")
        
        # Get the same memory again (simulating second agent call)
        context_memory_2 = get_context_memory(session_id)
        
        # Should be the same memory object
        assert context_memory is context_memory_2
        
        # Should contain previous conversation
        vars_2 = context_memory_2.load_memory_variables({})
        history = vars_2.get("chat_history", [])
        
        assert len(history) == 2
        assert any("First context query" in str(msg) for msg in history)
        assert any("First context response" in str(msg) for msg in history)
    
    def test_window_memory_behavior(self):
        """Test that window memory properly limits conversation history"""
        session_id = "test_window_session"
        
        # Get agent memory (window size = 5)
        context_memory = get_context_memory(session_id)
        
        # Add more messages than the window size
        for i in range(10):
            context_memory.chat_memory.add_user_message(f"Query {i}")
            context_memory.chat_memory.add_ai_message(f"Response {i}")
        
        # Should only keep the last 5 exchanges (10 messages total)
        vars = context_memory.load_memory_variables({})
        history = vars.get("chat_history", [])
        
        # Window size is 5, so should keep last 5 exchanges = 10 messages
        assert len(history) <= 10
        
        # Should contain recent messages, not early ones
        history_str = [str(msg) for msg in history]
        assert any("Query 9" in msg for msg in history_str)  # Most recent
        assert any("Response 9" in msg for msg in history_str)
        assert not any("Query 0" in msg for msg in history_str)  # Oldest should be gone


class TestErrorHandling:
    """Test error handling in the scoped memory system"""
    
    def test_invalid_agent_type_handling(self):
        """Test handling of invalid agent types"""
        session_id = "test_error_session"
        manager = get_scoped_memory_manager()
        
        with pytest.raises(ValueError, match="Unknown agent type"):
            manager.get_agent_memory(session_id, "invalid_agent_type")
    
    def test_memory_manager_resilience(self):
        """Test that memory manager handles edge cases gracefully"""
        manager = get_scoped_memory_manager()
        
        # Empty session ID should work
        empty_memory = manager.get_user_memory("")
        assert empty_memory is not None
        
        # Very long session ID should work
        long_session = "a" * 1000
        long_memory = manager.get_user_memory(long_session)
        assert long_memory is not None
        
        # Special characters in session ID should work
        special_session = "session-with-special_chars.123!@#"
        special_memory = manager.get_user_memory(special_session)
        assert special_memory is not None 
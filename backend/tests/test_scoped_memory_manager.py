"""
Unit tests for ScopedMemoryManager

Tests memory isolation, session management, and conversation scoping
to ensure agents only see their own conversation threads.
"""

import pytest
import time
from api.memory.scoped_memory_manager import (
    ScopedMemoryManager, 
    get_scoped_memory_manager,
    get_user_memory,
    get_agent_memory
)


class TestScopedMemoryManager:
    """Test the ScopedMemoryManager class functionality"""
    
    def setup_method(self):
        """Reset memory manager for each test"""
        # Create a fresh memory manager for each test
        self.memory_manager = ScopedMemoryManager()
    
    def test_memory_isolation_between_agents(self):
        """Test that different agents have isolated memory stores"""
        session_id = "test_session_1"
        
        # Get memory for different agents
        context_memory = self.memory_manager.get_agent_memory(session_id, "context")
        contract_memory = self.memory_manager.get_agent_memory(session_id, "contract")
        classifier_memory = self.memory_manager.get_agent_memory(session_id, "classifier")
        
        # Verify they are different memory objects
        assert context_memory is not contract_memory
        assert context_memory is not classifier_memory
        assert contract_memory is not classifier_memory
        
        # Add messages to context memory
        context_memory.chat_memory.add_user_message("Context agent query")
        context_memory.chat_memory.add_ai_message("Context agent response")
        
        # Verify other agents don't see context agent conversations
        contract_vars = contract_memory.load_memory_variables({})
        classifier_vars = classifier_memory.load_memory_variables({})
        
        assert len(contract_vars.get("chat_history", [])) == 0
        assert len(classifier_vars.get("chat_history", [])) == 0
    
    def test_user_memory_isolation_from_agents(self):
        """Test that user memory is isolated from agent memories"""
        session_id = "test_session_2"
        
        # Get user memory and agent memory
        user_memory = self.memory_manager.get_user_memory(session_id)
        context_memory = self.memory_manager.get_agent_memory(session_id, "context")
        
        # Verify they are different objects
        assert user_memory is not context_memory
        
        # Add user conversation
        user_memory.chat_memory.add_user_message("User question")
        user_memory.chat_memory.add_ai_message("Main agent response")
        
        # Verify context agent doesn't see user conversation
        context_vars = context_memory.load_memory_variables({})
        assert len(context_vars.get("chat_history", [])) == 0
        
        # Add context agent conversation
        context_memory.chat_memory.add_user_message("Main agent to context")
        context_memory.chat_memory.add_ai_message("Context agent response")
        
        # Verify user memory doesn't see agent conversation
        user_vars = user_memory.load_memory_variables({})
        user_messages = user_vars.get("chat_history", [])
        
        # Should only contain user ↔ main agent conversation
        assert len(user_messages) == 2
        assert any("User question" in str(msg) for msg in user_messages)
        assert not any("Main agent to context" in str(msg) for msg in user_messages)
    
    def test_session_isolation(self):
        """Test that different sessions have isolated memories"""
        session_1 = "test_session_A"
        session_2 = "test_session_B"
        
        # Get memories for different sessions
        user_memory_1 = self.memory_manager.get_user_memory(session_1)
        user_memory_2 = self.memory_manager.get_user_memory(session_2)
        
        # Verify they are different objects
        assert user_memory_1 is not user_memory_2
        
        # Add conversation to session 1
        user_memory_1.chat_memory.add_user_message("Session 1 message")
        
        # Verify session 2 doesn't see session 1 conversation
        session_2_vars = user_memory_2.load_memory_variables({})
        assert len(session_2_vars.get("chat_history", [])) == 0
    
    def test_session_activity_tracking(self):
        """Test that session activity is properly tracked"""
        session_id = "test_session_activity"
        
        # Initially no activity
        assert session_id not in self.memory_manager.session_activity
        
        # Access memory should update activity
        start_time = time.time()
        self.memory_manager.get_user_memory(session_id)
        end_time = time.time()
        
        # Verify activity was recorded
        assert session_id in self.memory_manager.session_activity
        activity_time = self.memory_manager.session_activity[session_id]
        assert start_time <= activity_time <= end_time
    
    def test_window_sizes(self):
        """Test that different memory types have appropriate window sizes"""
        session_id = "test_window_sizes"
        
        # User memory should have larger window (10)
        user_memory = self.memory_manager.get_user_memory(session_id)
        assert user_memory.k == 10
        
        # Agent memories should have smaller window (5)
        context_memory = self.memory_manager.get_agent_memory(session_id, "context")
        assert context_memory.k == 5
    
    def test_invalid_agent_type(self):
        """Test that invalid agent types raise appropriate errors"""
        session_id = "test_invalid_agent"
        
        with pytest.raises(ValueError, match="Unknown agent type"):
            self.memory_manager.get_agent_memory(session_id, "invalid_agent")
    
    def test_session_stats(self):
        """Test session statistics functionality"""
        # Initially empty
        stats = self.memory_manager.get_session_stats()
        assert stats["active_sessions"] == 0
        assert stats["total_memory_stores"] == 0
        
        # Add some sessions
        self.memory_manager.get_user_memory("session_1")
        self.memory_manager.get_agent_memory("session_1", "context")
        self.memory_manager.get_agent_memory("session_2", "contract")
        
        # Check updated stats
        stats = self.memory_manager.get_session_stats()
        assert stats["active_sessions"] == 2  # session_1 and session_2
        assert stats["user_conversations"] == 1
        assert stats["context_conversations"] == 1
        assert stats["contract_conversations"] == 1
        assert stats["classifier_conversations"] == 0
        assert stats["total_memory_stores"] == 3


class TestConvenienceFunctions:
    """Test the convenience functions and global manager"""
    
    def test_singleton_memory_manager(self):
        """Test that get_scoped_memory_manager returns singleton"""
        manager1 = get_scoped_memory_manager()
        manager2 = get_scoped_memory_manager()
        
        # Should be the same instance
        assert manager1 is manager2
    
    def test_convenience_functions(self):
        """Test get_user_memory and get_agent_memory convenience functions"""
        session_id = "test_convenience"
        
        # Test convenience functions
        user_memory = get_user_memory(session_id)
        agent_memory = get_agent_memory(session_id, "context")
        
        # Should return the same objects as direct manager calls
        manager = get_scoped_memory_manager()
        assert user_memory is manager.get_user_memory(session_id)
        assert agent_memory is manager.get_agent_memory(session_id, "context")


class TestConversationScoping:
    """Test that conversation scoping matches n8n architecture"""
    
    def setup_method(self):
        """Reset memory manager for each test"""
        self.memory_manager = ScopedMemoryManager()
    
    def test_context_agent_conversation_scoping(self):
        """Test ContextAgent only sees main agent ↔ context agent conversations"""
        session_id = "test_context_scoping"
        
        # Simulate n8n conversation flow
        user_memory = self.memory_manager.get_user_memory(session_id)
        context_memory = self.memory_manager.get_agent_memory(session_id, "context")
        contract_memory = self.memory_manager.get_agent_memory(session_id, "contract")
        
        # 1. User talks to main agent
        user_memory.chat_memory.add_user_message("My washing machine is broken")
        user_memory.chat_memory.add_ai_message("I'll help you with that issue")
        
        # 2. Main agent talks to context agent
        context_memory.chat_memory.add_user_message("washing machine broken")
        context_memory.chat_memory.add_ai_message("Need more details - which room, when did it start?")
        
        # 3. Main agent talks to contract agent
        contract_memory.chat_memory.add_user_message("appliance repair responsibility")
        contract_memory.chat_memory.add_ai_message("Landlord responsible for major appliances")
        
        # Verify isolation: Context agent should only see step 2
        context_vars = context_memory.load_memory_variables({})
        context_history = context_vars.get("chat_history", [])
        
        assert len(context_history) == 2  # Only main agent ↔ context agent
        assert any("washing machine broken" in str(msg) for msg in context_history)
        assert not any("My washing machine is broken" in str(msg) for msg in context_history)  # User message
        assert not any("appliance repair responsibility" in str(msg) for msg in context_history)  # Contract agent
    
    def test_multi_agent_conversation_isolation(self):
        """Test complete multi-agent conversation maintains proper isolation"""
        session_id = "test_multi_agent"
        
        # Get all memory channels
        user_memory = self.memory_manager.get_user_memory(session_id)
        context_memory = self.memory_manager.get_agent_memory(session_id, "context")
        contract_memory = self.memory_manager.get_agent_memory(session_id, "contract")
        classifier_memory = self.memory_manager.get_agent_memory(session_id, "classifier")
        
        # Simulate full conversation flow
        # User conversation
        user_memory.chat_memory.add_user_message("My heating isn't working")
        user_memory.chat_memory.add_ai_message("I'll investigate this for you")
        
        # Context agent conversation
        context_memory.chat_memory.add_user_message("heating not working")
        context_memory.chat_memory.add_ai_message("Need more context - when did it stop, any error codes?")
        
        # Contract agent conversation  
        contract_memory.chat_memory.add_user_message("heating system repair")
        contract_memory.chat_memory.add_ai_message("Landlord responsible for heating maintenance per section 5.1")
        
        # Classifier agent conversation
        classifier_memory.chat_memory.add_user_message("no heating")
        classifier_memory.chat_memory.add_ai_message("High priority - essential service, 24hr response required")
        
        # Verify each agent only sees its own conversation
        context_vars = context_memory.load_memory_variables({})
        contract_vars = contract_memory.load_memory_variables({})
        classifier_vars = classifier_memory.load_memory_variables({})
        user_vars = user_memory.load_memory_variables({})
        
        # Each should have exactly 2 messages (1 request + 1 response)
        assert len(context_vars.get("chat_history", [])) == 2
        assert len(contract_vars.get("chat_history", [])) == 2
        assert len(classifier_vars.get("chat_history", [])) == 2
        assert len(user_vars.get("chat_history", [])) == 2
        
        # Verify content isolation
        context_history = [str(msg) for msg in context_vars.get("chat_history", [])]
        contract_history = [str(msg) for msg in contract_vars.get("chat_history", [])]
        classifier_history = [str(msg) for msg in classifier_vars.get("chat_history", [])]
        user_history = [str(msg) for msg in user_vars.get("chat_history", [])]
        
        # Context agent should only see "heating not working" conversation
        assert any("heating not working" in msg for msg in context_history)
        assert not any("heating system repair" in msg for msg in context_history)
        assert not any("no heating" in msg for msg in context_history)
        assert not any("My heating isn't working" in msg for msg in context_history)
        
        # Contract agent should only see "heating system repair" conversation
        assert any("heating system repair" in msg for msg in contract_history)
        assert not any("heating not working" in msg for msg in contract_history)
        assert not any("no heating" in msg for msg in contract_history)
        
        # Classifier agent should only see "no heating" conversation
        assert any("no heating" in msg for msg in classifier_history)
        assert not any("heating not working" in msg for msg in classifier_history)
        assert not any("heating system repair" in msg for msg in classifier_history)
        
        # User should only see user ↔ main agent conversation
        assert any("My heating isn't working" in msg for msg in user_history)
        assert any("I'll investigate this for you" in msg for msg in user_history)
        assert not any("heating not working" in msg for msg in user_history)  # Agent conversation 
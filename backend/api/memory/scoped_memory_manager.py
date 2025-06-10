"""
Scoped Memory Manager for Agent Conversations

This module provides isolated memory channels for different types of agent interactions:
- User ↔ Main Agent conversations  
- Main Agent ↔ Context Agent conversations
- Main Agent ↔ Contract Agent conversations  
- Main Agent ↔ Classifier Agent conversations

Each channel maintains its own conversation history to prevent cross-contamination
between different agent roles, matching the n8n conversation scoping architecture.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Optional
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import BaseMessage


class ScopedMemoryManager:
    """
    Manages separate conversation channels for different agent interactions.
    
    This ensures that:
    - User conversations are isolated from agent-to-agent conversations
    - Each agent only sees its own conversation thread with the main agent
    - Memory doesn't leak between different conversation types
    - Session activity is tracked for cleanup purposes
    """
    
    def __init__(self):
        # Separate conversation channels - each stores session_id -> ConversationBufferWindowMemory
        self.user_conversations: Dict[str, ConversationBufferWindowMemory] = {}
        self.context_conversations: Dict[str, ConversationBufferWindowMemory] = {}  
        self.contract_conversations: Dict[str, ConversationBufferWindowMemory] = {}
        self.classifier_conversations: Dict[str, ConversationBufferWindowMemory] = {}
        
        # Session activity tracking for cleanup purposes
        self.session_activity: Dict[str, float] = {}
        
    def _update_session_activity(self, session_id: str) -> None:
        """Update the last activity timestamp for a session"""
        self.session_activity[session_id] = time.time()
        
    def _create_memory(self, window_size: int = 5) -> ConversationBufferWindowMemory:
        """Create a new conversation memory with specified window size"""
        return ConversationBufferWindowMemory(
            k=window_size,
            memory_key="chat_history",
            return_messages=True
        )
    
    def get_user_memory(self, session_id: str) -> ConversationBufferWindowMemory:
        """
        Get conversation memory for user ↔ main agent interactions.
        
        This channel contains:
        - User messages to the main agent
        - Main agent responses to the user
        
        This channel does NOT contain:
        - Agent-to-agent conversations
        - Internal agent deliberations
        """
        if session_id not in self.user_conversations:
            # Use larger window for user conversations (they're more important)
            self.user_conversations[session_id] = self._create_memory(window_size=10)
            
        self._update_session_activity(session_id)
        return self.user_conversations[session_id]
    
    def get_agent_memory(self, session_id: str, agent_type: str) -> ConversationBufferWindowMemory:
        """
        Get conversation memory for main agent ↔ specific agent interactions.
        
        Args:
            session_id: The session identifier
            agent_type: One of 'context', 'contract', 'classifier'
            
        Returns:
            ConversationBufferWindowMemory for that specific agent conversation
            
        This ensures each agent only sees its own conversation thread with the main agent:
        - ContextAgent sees only main agent ↔ context agent conversations
        - ContractAgent sees only main agent ↔ contract agent conversations  
        - ClassifierAgent sees only main agent ↔ classifier agent conversations
        """
        # Map agent types to their respective conversation stores
        agent_stores = {
            'context': self.context_conversations,
            'contract': self.contract_conversations, 
            'classifier': self.classifier_conversations
        }
        
        if agent_type not in agent_stores:
            raise ValueError(f"Unknown agent type: {agent_type}. Must be one of: {list(agent_stores.keys())}")
            
        store = agent_stores[agent_type]
        
        if session_id not in store:
            # Use smaller window for agent conversations (more focused)
            store[session_id] = self._create_memory(window_size=5)
            
        self._update_session_activity(session_id)
        return store[session_id]
    
    def get_session_stats(self) -> Dict[str, any]:
        """
        Get statistics about current memory usage and session activity.
        
        Returns:
            Dictionary with memory usage statistics
        """
        return {
            'active_sessions': len(self.session_activity),
            'user_conversations': len(self.user_conversations),
            'context_conversations': len(self.context_conversations),
            'contract_conversations': len(self.contract_conversations), 
            'classifier_conversations': len(self.classifier_conversations),
            'total_memory_stores': (
                len(self.user_conversations) + 
                len(self.context_conversations) + 
                len(self.contract_conversations) + 
                len(self.classifier_conversations)
            ),
            'oldest_session': min(self.session_activity.values()) if self.session_activity else None,
            'newest_session': max(self.session_activity.values()) if self.session_activity else None
        }
    
    def cleanup_expired_sessions(self, max_age_hours: int = 24) -> int:
        """
        Remove sessions that haven't been active for more than max_age_hours.
        
        Args:
            max_age_hours: Maximum age in hours before a session is considered expired
            
        Returns:
            Number of sessions cleaned up
            
        Note: Implementation will be added in Phase 3
        """
        # Placeholder for now - will implement in Phase 3
        cutoff_time = time.time() - (max_age_hours * 3600)
        expired_sessions = [
            session_id for session_id, last_activity 
            in self.session_activity.items() 
            if last_activity < cutoff_time
        ]
        
        # TODO: Implement actual cleanup in Phase 3
        print(f"[MEMORY MANAGER] Would clean up {len(expired_sessions)} expired sessions")
        return len(expired_sessions)


# Global singleton instance
_memory_manager: Optional[ScopedMemoryManager] = None

def get_scoped_memory_manager() -> ScopedMemoryManager:
    """
    Get the global scoped memory manager instance.
    
    This ensures all agents use the same memory manager instance,
    allowing proper conversation isolation and session management.
    """
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = ScopedMemoryManager()
        print("[MEMORY MANAGER] Initialized scoped memory manager")
    return _memory_manager


def get_user_memory(session_id: str) -> ConversationBufferWindowMemory:
    """Convenience function to get user memory for a session"""
    return get_scoped_memory_manager().get_user_memory(session_id)


def get_agent_memory(session_id: str, agent_type: str) -> ConversationBufferWindowMemory:
    """Convenience function to get agent memory for a session"""
    return get_scoped_memory_manager().get_agent_memory(session_id, agent_type) 
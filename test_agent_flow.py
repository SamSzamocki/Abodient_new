#!/usr/bin/env python3
"""
Test Agent Flow - Check if Main Agent Calls Tools
=================================================

This script tests if the main agent properly calls the context and contract agents
when processing a tenant query.
"""

import os
import sys

# Load environment variables from backend/.env
def load_env():
    """Load environment variables from backend/.env"""
    env_path = "backend/.env"
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    else:
        print("⚠️  Warning: backend/.env not found")

# Load environment before any imports
load_env()

# Add the backend directory to the path
sys.path.append('backend/api')

def test_main_agent():
    """Test the main agent with a typical tenant query."""
    
    print("🧪 Testing Main Agent Tool Calling...")
    
    # Import after adding path
    from agents.main_agent import handle_message
    from database import get_db
    
    # Test query that should trigger context agent and contract agent
    test_query = "I have a leak in my bathroom ceiling, water is dripping down. What should I do?"
    test_session = "test-session-123"
    
    print(f"📝 Test Query: {test_query}")
    print(f"🔧 Session ID: {test_session}")
    print("\n" + "="*60)
    
    try:
        # Get database session (mock)
        db = next(get_db())
        
        # Call the main agent
        print("🤖 Calling main agent...")
        result = handle_message(db, test_session, test_query)
        
        print("\n📊 RESULT:")
        print(f"Chat Output: {result.get('chat_output', 'No output')}")
        print(f"Query Summary: {result.get('query_summary', 'No summary')}")
        print(f"Actions: {result.get('actions', [])}")
        
        # Check if the output contains evidence of tool calls
        output = result.get('chat_output', '').lower()
        
        print("\n🔍 ANALYSIS:")
        if 'context' in output or 'clarify' in output:
            print("✅ Likely called Context Agent")
        else:
            print("❌ No evidence of Context Agent call")
            
        if 'contract' in output or 'landlord responsible' in output:
            print("✅ Likely called Contract Agent")
        else:
            print("❌ No evidence of Contract Agent call")
            
        if 'urgent' in output or 'priority' in output:
            print("✅ Likely called Classifier Agent")
        else:
            print("❌ No evidence of Classifier Agent call")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

def test_individual_tools():
    """Test each tool individually."""
    
    print("\n" + "="*60)
    print("🔧 Testing Individual Tools...")
    
    try:
        from agents.tools import ContextAgentTool, ContractAgentTool, ClassifierAgentTool
        
        test_query = "bathroom ceiling leak with water dripping"
        
        # Test Context Agent Tool
        print("\n1️⃣ Testing Context Agent Tool:")
        context_tool = ContextAgentTool()
        try:
            context_result = context_tool._run(test_query)
            print(f"✅ Context Agent Result: {str(context_result)[:200]}...")
        except Exception as e:
            print(f"❌ Context Agent Error: {e}")
        
        # Test Contract Agent Tool  
        print("\n2️⃣ Testing Contract Agent Tool:")
        contract_tool = ContractAgentTool()
        try:
            contract_result = contract_tool._run(test_query)
            print(f"✅ Contract Agent Result: {str(contract_result)[:200]}...")
        except Exception as e:
            print(f"❌ Contract Agent Error: {e}")
            
        # Test Classifier Agent Tool
        print("\n3️⃣ Testing Classifier Agent Tool:")
        classifier_tool = ClassifierAgentTool()
        try:
            classifier_result = classifier_tool._run(test_query)
            print(f"✅ Classifier Agent Result: {str(classifier_result)[:200]}...")
        except Exception as e:
            print(f"❌ Classifier Agent Error: {e}")
            
    except Exception as e:
        print(f"❌ Tool Import Error: {e}")

if __name__ == "__main__":
    print("🚀 Starting Agent Flow Tests...")
    
    # Test 1: Main agent orchestration
    test_main_agent()
    
    # Test 2: Individual tools
    test_individual_tools()
    
    print("\n✅ Tests completed!") 
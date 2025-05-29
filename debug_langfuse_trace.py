#!/usr/bin/env python3
"""
Langfuse Trace Debugger for Abodient Agent Orchestration

Usage: 
  python debug_langfuse_trace.py <trace_id>         # Orchestration-focused output
  python debug_langfuse_trace.py <trace_id> --full  # Full input/output data
  python debug_langfuse_trace.py <trace_id> --raw   # All observations (debug mode)
"""

import sys
import os
from langfuse import Langfuse

def load_env():
    """Load environment variables from backend/.env"""
    env_path = "backend/.env"
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

def analyze_trace(trace_id, show_full=False, show_raw=False):
    """Analyze a Langfuse trace and return structured debugging information"""
    load_env()
    
    langfuse = Langfuse()
    trace = langfuse.get_trace(trace_id)
    
    print("=" * 80)
    print(f"TRACE ANALYSIS: {trace_id}")
    if show_full:
        print("(FULL DATA MODE)")
    elif show_raw:
        print("(RAW DEBUG MODE)")
    print("=" * 80)
    
    # Basic trace info
    print(f"📝 Name: {trace.name}")
    print(f"⏰ Start: {trace.timestamp}")
    print(f"👤 User: {trace.user_id}")
    print(f"🔗 Session: {trace.session_id}")
    print(f"📊 Total Observations: {len(trace.observations)}")
    
    # Input/Output (truncated or full based on flag)
    if show_full:
        print(f"\n📥 FULL INPUT:")
        print(f"   {str(trace.input)}")
        
        print(f"\n📤 FULL OUTPUT:")
        print(f"   {str(trace.output)}")
    else:
        print(f"\n📥 INPUT (first 200 chars):")
        print(f"   {str(trace.input)[:200]}...")
        
        print(f"\n📤 OUTPUT (first 200 chars):")
        print(f"   {str(trace.output)[:200]}...")
    
    # 🤖 AGENT ORCHESTRATION - The most important section
    print(f"\n🤖 AGENT ORCHESTRATION:")
    agent_tools = [obs for obs in trace.observations if any(keyword in obs.name for keyword in 
                   ['ContextAgent', 'contractAgent', 'classifierAgent', 'context_agent', 'contract_agent', 'classifier_agent'])]
    
    if agent_tools:
        print(f"   ✅ {len(agent_tools)} agents called:")
        for i, obs in enumerate(sorted(agent_tools, key=lambda x: x.start_time), 1):
            duration = ""
            if obs.start_time and obs.end_time:
                duration = f" ({(obs.end_time - obs.start_time).total_seconds():.2f}s)"
            
            print(f"   Step {i}: {obs.name}{duration}")
            
            if show_full:
                print(f"      FULL INPUT:")
                print(f"         {str(obs.input)}")
                print(f"      FULL OUTPUT:")
                print(f"         {str(obs.output)}")
            else:
                print(f"      Input: {str(obs.input)[:100]}...")
                print(f"      Output: {str(obs.output)[:150]}...")
            print()
    else:
        print("   ❌ No agent tools called!")
        print("      This means the LLM responded directly without orchestration")
    
    # 🧠 LLM DECISION MAKING
    print(f"\n🧠 LLM DECISION MAKING:")
    generations = [obs for obs in trace.observations if obs.type == 'GENERATION']
    
    if generations:
        print(f"   💭 {len(generations)} LLM calls made:")
        for i, gen in enumerate(generations, 1):
            model = getattr(gen, 'model', 'Unknown')
            usage = getattr(gen, 'usage_details', {})
            tokens = f"{usage.get('input', '?')}→{usage.get('output', '?')}" if usage else "?"
            
            print(f"   Call {i}: {gen.name} ({model}) [{tokens} tokens]")
            
            if show_full:
                print(f"      FULL INPUT:")
                print(f"         {str(gen.input)}")
                print(f"      FULL OUTPUT:")
                print(f"         {str(gen.output)}")
            else:
                # Show just the decision/output for orchestration context
                print(f"      Decision: {str(gen.output)[:200]}...")
            print()
    else:
        print("   ❌ No LLM calls made!")
        print("      This is unusual - check if trace capture is working")
    
    # 🎛️ SYSTEM CONFIGURATION
    print(f"\n🎛️ SYSTEM CONFIGURATION:")
    chat_prompt = [obs for obs in trace.observations if obs.name == 'ChatPromptTemplate']
    
    if chat_prompt:
        prompt_obs = chat_prompt[0]
        output_str = str(prompt_obs.output)
        
        # Extract system message content
        if 'SystemMessage' in output_str and 'content=' in output_str:
            # Simple extraction of system prompt
            start = output_str.find("content='") + 9
            end = output_str.find("'", start + 100)  # Find next quote after some content
            if start > 8 and end > start:
                system_content = output_str[start:end]
                print(f"   ✅ System prompt loaded: {system_content[:100]}...")
            else:
                print(f"   ⚠️  System prompt format unclear")
        else:
            print(f"   ❌ No system prompt found")
            
        if show_full:
            print(f"   FULL PROMPT DATA:")
            print(f"      Input: {str(prompt_obs.input)}")
            print(f"      Output: {str(prompt_obs.output)}")
    else:
        print("   ❌ No ChatPromptTemplate found")
    
    # ⚡ PERFORMANCE ANALYSIS
    print(f"\n⚡ PERFORMANCE ANALYSIS:")
    if trace.observations:
        start_time = min(obs.start_time for obs in trace.observations if obs.start_time)
        end_time = max(obs.end_time for obs in trace.observations if obs.end_time)
        total_duration = (end_time - start_time).total_seconds()
        print(f"   Total Duration: {total_duration:.2f} seconds")
        
        # Agent timing breakdown
        if agent_tools:
            agent_time = sum((obs.end_time - obs.start_time).total_seconds() 
                           for obs in agent_tools if obs.start_time and obs.end_time)
            print(f"   Agent Time: {agent_time:.2f}s ({agent_time/total_duration*100:.1f}%)")
            
        # Token usage summary
        if generations:
            total_input_tokens = sum(gen.usage_details.get('input', 0) for gen in generations if gen.usage_details)
            total_output_tokens = sum(gen.usage_details.get('output', 0) for gen in generations if gen.usage_details)
            print(f"   Tokens Used: {total_input_tokens}→{total_output_tokens} (total: {total_input_tokens + total_output_tokens})")
    
    # 🔧 TECHNICAL DETAILS (only if requested)
    if show_raw:
        print(f"\n🔧 ALL OBSERVATIONS (RAW DEBUG):")
        for obs in sorted(trace.observations, key=lambda x: x.start_time or 0):
            print(f"   {obs.name} ({obs.type}) - {obs.start_time}")
            if show_full:
                print(f"      Input: {str(obs.input)[:200]}...")
                print(f"      Output: {str(obs.output)[:200]}...")
    
    print("=" * 80)

if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage:")
        print("  python debug_langfuse_trace.py <trace_id>         # Orchestration-focused output")
        print("  python debug_langfuse_trace.py <trace_id> --full  # Full input/output data")
        print("  python debug_langfuse_trace.py <trace_id> --raw   # All observations (debug mode)")
        sys.exit(1)
    
    trace_id = sys.argv[1]
    show_full = len(sys.argv) == 3 and sys.argv[2] == '--full'
    show_raw = len(sys.argv) == 3 and sys.argv[2] == '--raw'
    
    try:
        analyze_trace(trace_id, show_full, show_raw)
    except Exception as e:
        print(f"Error analyzing trace: {e}")
        sys.exit(1) 
#!/usr/bin/env python3
"""
Debug Agent Orchestration with Langfuse API
============================================

This script has two modes for analyzing Langfuse traces:

LIGHTWEIGHT MODE (default - follows rate limit best practices):
    python debug_orchestration.py
    - Analyzes only TODAY's traces (max 5)
    - Minimal API calls (~5-10 total)
    - Quick overview of recent agent patterns
    
FULL ANALYSIS MODE (use sparingly due to rate limits):
    python debug_orchestration.py --full
    - Deep analysis of multiple traces
    - Higher API usage - expect rate limits
    - Detailed investigation mode

Requirements:
    pip install langfuse pandas
"""

import os
import sys
import argparse
from langfuse import Langfuse
from datetime import datetime, timedelta
import pandas as pd

def load_env():
    """Load environment variables from backend/.env"""
    env_path = "backend/.env"
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

def get_today_start():
    """Get the start of today in UTC for filtering"""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return today

def lightweight_trace_analysis():
    """
    Lightweight analysis following the debugging guide:
    - TODAY's traces only
    - Max 5 traces
    - Minimal API calls
    - Focus on recent patterns
    """
    load_env()
    langfuse = Langfuse()
    
    today_start = get_today_start()
    print(f"🔍 LIGHTWEIGHT MODE: Analyzing TODAY's traces only ({today_start.strftime('%Y-%m-%d')})")
    print("📊 Following rate limit best practices...")
    
    # Get recent traces from today only
    traces = langfuse.fetch_traces(
        limit=5,  # Keep it small to avoid rate limits
        from_timestamp=today_start
    )
    
    if not traces.data:
        print("❌ No traces found for today!")
        print("💡 This might indicate:")
        print("   - No recent activity")
        print("   - Clock/timezone issues")
        print("   - Langfuse connection problems")
        return
    
    print(f"✅ Found {len(traces.data)} traces from today")
    
    # Quick analysis - just trace-level info (minimal API calls)
    agent_patterns = {
        "no_agents": 0,
        "classifier_only": 0, 
        "full_orchestration": 0,
        "partial_orchestration": 0
    }
    
    trace_list = []
    
    for i, trace in enumerate(traces.data):
        print(f"\n📋 Trace {i+1}: {trace.id[:8]}... ({trace.timestamp})")
        
        # Get basic trace info only (1 API call per trace)
        try:
            observations = langfuse.fetch_observations(trace_id=trace.id, limit=50)
            
            # Quick agent detection - improved logic
            agent_calls = []
            unique_agents = set()
            
            for obs in observations.data:
                obs_name = obs.name.lower()
                # More comprehensive agent detection
                if "classifier" in obs_name or "classifierAgent" in obs.name:
                    agent_calls.append("classifier")
                    unique_agents.add("classifier")
                elif "context" in obs_name and "agent" in obs_name:
                    agent_calls.append("context_agent")
                    unique_agents.add("context_agent")
                elif "contract" in obs_name and "agent" in obs_name:
                    agent_calls.append("contract_agent")
                    unique_agents.add("contract_agent")
                elif "main_agent" in obs_name:
                    agent_calls.append("main_agent")
                    unique_agents.add("main_agent")
            
            # Remove duplicates while preserving order
            seen = set()
            unique_agent_calls = []
            for agent in agent_calls:
                if agent not in seen:
                    unique_agent_calls.append(agent)
                    seen.add(agent)
            
            # Categorize orchestration pattern based on unique agents called
            if not unique_agents:
                agent_patterns["no_agents"] += 1
                pattern = "❌ No agents called"
            elif unique_agents == {"classifier"}:
                agent_patterns["classifier_only"] += 1
                pattern = "⚠️  Classifier only"
            elif len(unique_agents & {"context_agent", "contract_agent", "classifier"}) >= 3:
                agent_patterns["full_orchestration"] += 1
                pattern = "✅ Full orchestration"
            elif len(unique_agents & {"context_agent", "contract_agent", "classifier"}) >= 2:
                agent_patterns["partial_orchestration"] += 1
                pattern = f"⚡ Partial: {' → '.join(unique_agent_calls)}"
            else:
                agent_patterns["partial_orchestration"] += 1
                pattern = f"⚡ Partial: {' → '.join(unique_agent_calls)}"
            
            print(f"   Pattern: {pattern}")
            print(f"   Agents: {' → '.join(unique_agent_calls) if unique_agent_calls else 'None'}")
            print(f"   Debug: Found {len(observations.data)} observations, unique agents: {unique_agents}")
            
            trace_list.append({
                "id": trace.id,
                "timestamp": trace.timestamp,
                "pattern": pattern,
                "agents": unique_agent_calls
            })
            
        except Exception as e:
            print(f"   ⚠️  Error analyzing trace: {e}")
    
    # Summary
    print(f"\n🎯 TODAY'S ORCHESTRATION SUMMARY:")
    print(f"   ❌ No agents: {agent_patterns['no_agents']}")
    print(f"   ⚠️  Classifier only: {agent_patterns['classifier_only']}")
    print(f"   ⚡ Partial orchestration: {agent_patterns['partial_orchestration']}")
    print(f"   ✅ Full orchestration: {agent_patterns['full_orchestration']}")
    
    # Quick recommendations
    print(f"\n💡 QUICK RECOMMENDATIONS:")
    if agent_patterns["no_agents"] > 0:
        print(f"   - {agent_patterns['no_agents']} traces had NO agent calls - LLM responding directly")
        print(f"   - Check system prompt agent tool configuration")
    
    if agent_patterns["classifier_only"] > 0:
        print(f"   - {agent_patterns['classifier_only']} traces only used classifier")
        print(f"   - May indicate main agent not being triggered")
    
    if agent_patterns["full_orchestration"] == 0:
        print(f"   - ⚠️  NO full orchestration today - this may indicate a problem")
    
    # Return most recent trace ID for further analysis
    if trace_list:
        most_recent = trace_list[0]
        print(f"\n🎯 MOST RECENT TRACE: {most_recent['id'][:8]}...")
        print(f"   Use: python debug_langfuse_trace.py {most_recent['id']}")
        return most_recent['id']
    
    return None

def analyze_agent_orchestration(hours_back=24, max_traces=50):
    """
    FULL ANALYSIS MODE - Original function with heavy API usage
    
    Args:
        hours_back: How many hours back to analyze traces
        max_traces: Maximum number of traces to analyze
    
    Returns:
        Dictionary with orchestration analysis
    """
    load_env()
    langfuse = Langfuse()
    
    print(f"🔍 FULL MODE: Analyzing last {hours_back} hours...")
    print("⚠️  WARNING: High API usage - expect rate limits")
    
    # Fetch recent traces
    traces = langfuse.fetch_traces(
        limit=max_traces,
        from_timestamp=datetime.now() - timedelta(hours=hours_back)
    )
    
    analysis = {
        "total_traces": len(traces.data),
        "main_agent_calls": 0,
        "context_agent_calls": 0,
        "contract_agent_calls": 0,
        "classifier_agent_calls": 0,
        "orchestration_patterns": [],
        "missing_agent_calls": [],
        "trace_details": []
    }
    
    print(f"📊 Found {len(traces.data)} traces to analyze\n")
    
    for trace in traces.data:
        trace_detail = {
            "trace_id": trace.id,
            "timestamp": trace.timestamp,
            "agents_called": [],
            "observations": []
        }
        
        # Fetch all observations for this trace
        observations = langfuse.fetch_observations(trace_id=trace.id)
        
        agent_sequence = []
        
        for obs in observations.data:
            trace_detail["observations"].append({
                "name": obs.name,
                "type": obs.type,
                "input": str(obs.input)[:100] + "..." if obs.input else None,
                "output": str(obs.output)[:100] + "..." if obs.output else None
            })
            
            # Check for agent calls based on observation names
            if "main_agent" in obs.name.lower():
                analysis["main_agent_calls"] += 1
                agent_sequence.append("main_agent")
            elif "context_agent" in obs.name.lower():
                analysis["context_agent_calls"] += 1
                agent_sequence.append("context_agent")
            elif "contract_agent" in obs.name.lower():
                analysis["contract_agent_calls"] += 1
                agent_sequence.append("contract_agent")
            elif "classifier" in obs.name.lower():
                analysis["classifier_agent_calls"] += 1
                agent_sequence.append("classifier_agent")
        
        trace_detail["agents_called"] = agent_sequence
        analysis["orchestration_patterns"].append(agent_sequence)
        analysis["trace_details"].append(trace_detail)
        
        # Check for expected orchestration pattern
        if "main_agent" in agent_sequence and "context_agent" in agent_sequence:
            if "contract_agent" not in agent_sequence:
                analysis["missing_agent_calls"].append({
                    "trace_id": trace.id,
                    "issue": "Context agent called but contract agent missing",
                    "sequence": agent_sequence
                })
    
    return analysis

def print_orchestration_report(analysis):
    """Print a detailed orchestration analysis report."""
    
    print("=" * 60)
    print("🤖 AGENT ORCHESTRATION ANALYSIS REPORT")
    print("=" * 60)
    
    print(f"\n📈 SUMMARY:")
    print(f"Total traces analyzed: {analysis['total_traces']}")
    print(f"Main agent calls: {analysis['main_agent_calls']}")
    print(f"Context agent calls: {analysis['context_agent_calls']}")
    print(f"Contract agent calls: {analysis['contract_agent_calls']}")
    print(f"Classifier agent calls: {analysis['classifier_agent_calls']}")
    
    print(f"\n🚨 POTENTIAL ISSUES:")
    if analysis['missing_agent_calls']:
        for issue in analysis['missing_agent_calls']:
            print(f"- Trace {issue['trace_id'][:8]}...: {issue['issue']}")
            print(f"  Sequence: {' → '.join(issue['sequence'])}")
    else:
        print("- No obvious orchestration issues detected")
    
    print(f"\n🔄 ORCHESTRATION PATTERNS:")
    patterns = {}
    for pattern in analysis['orchestration_patterns']:
        pattern_str = ' → '.join(pattern) if pattern else 'No agents called'
        patterns[pattern_str] = patterns.get(pattern_str, 0) + 1
    
    for pattern, count in sorted(patterns.items(), key=lambda x: x[1], reverse=True):
        print(f"- {pattern}: {count} times")
    
    print(f"\n🔍 DETAILED TRACE ANALYSIS:")
    for i, trace in enumerate(analysis['trace_details'][:5]):  # Show first 5 traces
        print(f"\nTrace {i+1}: {trace['trace_id'][:8]}...")
        print(f"  Agents: {' → '.join(trace['agents_called']) if trace['agents_called'] else 'None'}")
        print(f"  Observations: {len(trace['observations'])}")
        
        # Show key observations
        for obs in trace['observations'][:3]:  # Show first 3 observations
            print(f"    - {obs['name']} ({obs['type']})")

def debug_specific_trace(trace_id):
    """
    Debug a specific trace in detail to understand orchestration flow.
    
    Args:
        trace_id: The specific trace ID to analyze
    """
    load_env()
    langfuse = Langfuse()
    
    print(f"\n🔬 DETAILED TRACE ANALYSIS: {trace_id}")
    print("-" * 50)
    
    # Fetch the specific trace
    trace = langfuse.fetch_trace(trace_id)
    observations = langfuse.fetch_observations(trace_id=trace_id)
    
    print(f"Trace timestamp: {trace.timestamp}")
    print(f"Total observations: {len(observations.data)}")
    
    print(f"\n📋 OBSERVATION SEQUENCE:")
    for i, obs in enumerate(observations.data, 1):
        print(f"{i:2d}. {obs.name} ({obs.type})")
        if obs.input:
            input_preview = str(obs.input)[:200].replace('\n', ' ')
            print(f"    Input: {input_preview}...")
        if obs.output:
            output_preview = str(obs.output)[:200].replace('\n', ' ')
            print(f"    Output: {output_preview}...")
        print()

def find_problematic_traces():
    """Find traces where main agent doesn't call contract agent."""
    load_env()
    langfuse = Langfuse()
    
    print("🔍 Finding traces where contract agent should be called but isn't...")
    
    # This is a more sophisticated analysis
    traces = langfuse.fetch_traces(limit=100)
    problematic = []
    
    for trace in traces.data:
        observations = langfuse.fetch_observations(trace_id=trace.id)
        
        has_main = False
        has_context = False
        has_contract = False
        
        for obs in observations.data:
            if "main_agent" in obs.name.lower():
                has_main = True
            elif "context_agent" in obs.name.lower():
                has_context = True
            elif "contract_agent" in obs.name.lower():
                has_contract = True
        
        # If main and context called but not contract, that's suspicious
        if has_main and has_context and not has_contract:
            problematic.append(trace.id)
    
    print(f"Found {len(problematic)} potentially problematic traces:")
    for trace_id in problematic[:5]:  # Show first 5
        print(f"- {trace_id}")
    
    return problematic

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Debug agent orchestration with Langfuse')
    parser.add_argument('--full', action='store_true', 
                       help='Run full analysis mode (high API usage)')
    
    args = parser.parse_args()
    
    try:
        if args.full:
            print("🚨 RUNNING FULL ANALYSIS MODE")
            print("⚠️  This uses many API calls and will likely hit rate limits!")
            print()
            
            # Original heavy analysis
            analysis = analyze_agent_orchestration(hours_back=24, max_traces=20)
            print_orchestration_report(analysis)
            
            # Find specific problematic traces
            print("\n" + "=" * 60)
            problematic_traces = find_problematic_traces()
            
            if problematic_traces:
                print(f"\n🔬 Analyzing first problematic trace in detail...")
                debug_specific_trace(problematic_traces[0])
            
            print(f"\n💡 RECOMMENDATIONS:")
            print(f"1. Check why main agent isn't calling contract agent")
            print(f"2. Review agent routing logic in main_agent.py")
            print(f"3. Verify contract agent is properly registered")
            print(f"4. Check if user queries should trigger contract agent")
        else:
            print("⚡ RUNNING LIGHTWEIGHT MODE (default)")
            print("✅ Rate limit friendly - analyzing today's traces only")
            print()
            
            # New lightweight analysis
            recent_trace_id = lightweight_trace_analysis()
            
            if recent_trace_id:
                print(f"\n🔍 Next step: Analyze the most recent trace with:")
                print(f"   python debug_langfuse_trace.py {recent_trace_id}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Make sure your Langfuse credentials are set correctly.") 
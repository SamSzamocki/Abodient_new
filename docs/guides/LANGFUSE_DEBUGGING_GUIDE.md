# Langfuse Trace Debugging Guide

## ⚡ **GOLDEN RULE**: Always Focus on Recent Traces

- **Default to TODAY's traces only** - past traces may contain bugs that have been fixed
- **State date range clearly** when debugging so it can be adjusted if needed  
- Recent traces reflect current system behavior, older traces may be misleading

---

## 🚦 Rate Limit Management

**Langfuse has API rate limits** - expect 5-10 minute cooldowns between heavy analysis sessions

### API Call Analysis by Debugging Approach:

| Debugging Task | API Calls | Time to Limit | Efficiency |
|----------------|-----------|---------------|------------|
| Single trace analysis | 1-2 calls | Very Low | ✅ Efficient |
| Lightweight orchestration (default) | 5-10 calls | Low | ✅ Good |
| Full trace with `--full` flag | 1-2 calls | Low | ✅ Good |
| Full orchestration scan | 20-40 calls | **HIGH** | ❌ Rate limit risk |

### Efficient Debugging Strategy:
1. **Get today's traces first** (lightweight mode by default) 
2. **Analyze most recent trace only** - this usually shows current behavior
3. **Use targeted trace analysis** instead of bulk orchestration reports
4. **Wait 5-10 minutes between intensive API sessions**

---

## 📋 Key Information We Extract from Traces

### Primary Focus Areas:
1. **Agent Orchestration**: Which agents called, in what order, with what inputs/outputs
2. **LLM Decision Making**: What the main LLM decided to do (call agents vs direct response)
3. **System Configuration**: Which system prompt/context was used
4. **Performance Timing**: How long each step took
5. **Error Detection**: Failed agent calls, timeouts, exceptions

### What Constitutes "Sufficient" Trace Information:
- ✅ **Agent sequence and timing** (primary goal)
- ✅ **Agent inputs/outputs** (truncated is usually fine, full when debugging specific agent)
- ✅ **LLM reasoning** that led to agent calls
- ✅ **System prompt confirmation** 
- ⚠️ **Full raw data** only needed for deep debugging specific issues

---

## 🔧 Available Debugging Commands

### Quick Commands for Efficient Debugging:
```bash
# Get TODAY's traces overview (LIGHTWEIGHT - default mode, ~5-10 calls)
python debug_orchestration.py

# Analyze specific recent trace (targeted, ~1-2 API calls)
python debug_langfuse_trace.py <trace_id>

# Get full data only when needed (still ~1-2 API calls)
python debug_langfuse_trace.py <trace_id> --full

# Raw debug mode for technical issues (~1-2 API calls)
python debug_langfuse_trace.py <trace_id> --raw

# ONLY for deep investigation (HIGH API usage - expect rate limits!)
python debug_orchestration.py --full
```

### Command Decision Tree:
1. **Start with**: `debug_orchestration.py` (lightweight mode - today's traces only)
2. **Then focus on**: Most recent trace with `debug_langfuse_trace.py <id>`
3. **Use `--full` flag**: Only when debugging specific agent input/output issues
4. **Use `--raw` flag**: Only for technical/system debugging

---

## 🚀 Debugging Workflow Checklist

### Before You Start:
- [ ] **Specify date focus**: "Analyzing traces from today..." 
- [ ] **Check recent activity**: Look for traces from last 2-4 hours
- [ ] **Identify the issue timeframe**: When did the behavior start?

### Step-by-Step Process:
1. **Get recent trace overview**:
   ```bash
   python debug_orchestration.py
   ```
   - Automatically analyzes TODAY's traces only
   - Rate limit friendly (5-10 API calls max)
   - Shows orchestration patterns

2. **Target most recent relevant trace**:
   ```bash
   python debug_langfuse_trace.py <most_recent_trace_id>
   ```
   - Focus on agent orchestration section
   - Check if agents were called as expected

3. **Drill down if needed**:
   ```bash
   python debug_langfuse_trace.py <trace_id> --full
   ```
   - Only if you need to see specific agent inputs/outputs
   - Use when debugging agent behavior, not orchestration logic

### Rate Limit Recovery:
- **Wait time**: 5-10 minutes typical reset
- **Check status**: Try small API call first (`debug_langfuse_trace.py <id>`)
- **Batch efficiently**: Get all needed info in single session

---

## 💡 Pro Tips

### For Regular Debugging:
- **Start narrow**: Single recent trace > bulk analysis
- **State assumptions**: "Looking at today's traces to avoid fixed bugs..."
- **Focus on differences**: Compare current behavior to expected behavior

### For Deep Investigation:
- **Use timeframes**: "Traces between 2pm-4pm today when issue occurred"
- **Compare good vs bad**: Find working trace + broken trace from same time period
- **Check agent sequence**: Often the issue is missing agent call or wrong order

### For Performance Analysis:
- **Recent traces only**: Performance fixes won't show in old traces
- **Agent timing breakdown**: Look for unusually slow agent calls
- **Token usage patterns**: Sudden increases might indicate prompt issues

---

## 🚨 Common Pitfalls

❌ **Don't**: Analyze traces from days/weeks ago without checking recent ones first
❌ **Don't**: Use `debug_orchestration.py --full` unless absolutely needed for deep investigation
❌ **Don't**: Use `--full` flag unless you specifically need full input/output data
❌ **Don't**: Ignore rate limits - wait between intensive sessions

✅ **Do**: Use `debug_orchestration.py` (lightweight mode) by default
✅ **Do**: Focus on recent traces first
✅ **Do**: Use targeted analysis for specific trace IDs  
✅ **Do**: State your time range assumptions clearly
✅ **Do**: Wait 5-10 minutes after hitting rate limits

---

*Last updated: 2025-01-27 based on troubleshooting session* 
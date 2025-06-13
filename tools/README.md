# Development Tools

This directory contains all development, debugging, and system management tools for Abodient.

## Directory Structure

### 🔧 `/debug/` - Debugging & Analysis Tools
- `debug_orchestration.py` - Analyze Langfuse traces and agent orchestration patterns
- `debug_langfuse_trace.py` - Deep dive analysis of specific Langfuse traces

**Usage Examples:**
```bash
# Quick analysis of today's traces
python tools/debug/debug_orchestration.py

# Detailed trace analysis
python tools/debug/debug_langfuse_trace.py <trace_id>
```

### 🚀 `/system/` - System Management
- `run_system.py` - Unified system startup and testing script

**Usage Examples:**
```bash
# Start full system
python tools/system/run_system.py

# Backend only
python tools/system/run_system.py --backend

# Test agent functionality  
python tools/system/run_system.py --test
```

### 🧪 `/testing/` - Test Utilities
*Reserved for future test management tools*

## Quick Commands

From project root:
```bash
# Debug latest traces
python tools/debug/debug_orchestration.py

# Start system
python tools/system/run_system.py

# Run memory tests
cd backend && python -m pytest tests/memory/ -v

# Run all tests
cd backend && python -m pytest tests/ -v
``` 
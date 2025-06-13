# Test Suite Organization

This directory contains all tests for the Abodient backend, organized by category.

## Directory Structure

### 🧪 `/unit/` - Unit Tests
Individual component testing with minimal dependencies:
- `langfuse_test.py` - Langfuse connectivity testing

### 🔗 `/integration/` - Integration Tests  
Multi-component testing and system workflows:
- `test_agent_integration.py` - Full agent workflow testing
- `test_agent_flow.py` - Agent orchestration testing

### 🧠 `/memory/` - Memory System Tests
Memory architecture and scoped memory testing:
- `test_scoped_memory_manager.py` - Core memory manager functionality
- `test_memory_integration.py` - Memory integration testing  
- `test_scoped_memory_simple.py` - Simplified memory testing
- `test_memory_orchestration_simple.py` - Memory orchestration testing

## Running Tests

### All Tests
```bash
cd backend
python -m pytest tests/ -v
```

### By Category
```bash
# Unit tests only
python -m pytest tests/unit/ -v

# Integration tests only  
python -m pytest tests/integration/ -v

# Memory system tests only
python -m pytest tests/memory/ -v
```

### Specific Test Files
```bash
# Memory manager core functionality
python -m pytest tests/memory/test_scoped_memory_manager.py -v

# Quick memory verification
python tests/memory/test_scoped_memory_simple.py
```

## Test Categories

- **Unit Tests**: Fast, isolated, minimal dependencies
- **Integration Tests**: Agent workflows, API endpoints, full system behavior
- **Memory Tests**: Scoped memory architecture, session isolation, conversation channels 
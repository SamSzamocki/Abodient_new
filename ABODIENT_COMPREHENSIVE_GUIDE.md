# Abodient: AI-Powered Property Management Support System - Comprehensive Codebase Documentation

---

## 🚀 AI Assistant Initialization Protocol

### READ THIS FIRST: Getting Fully Contextualized

**If you're an AI assistant starting fresh with this project, follow these steps in order:**

#### Step 0: Read Recent Changes (CRITICAL)
**Before proceeding with any other steps, you MUST read the recent change logs:**
- Read `RECENT_CHANGE_LOGS.md` to understand what changes have been made recently
- This will help you understand the current state and avoid redoing work
- Pay special attention to any ongoing issues or incomplete work mentioned

#### Step 1: Read This Entire Document
This comprehensive guide contains all architectural details, agent specifications, API schemas, and development guidelines. Read it completely before proceeding.

#### Step 2: Repository Deep Dive (REQUIRED)
After reading this guide, you MUST explore the actual codebase to understand implementation details:

```bash
# Key directories to examine:
- backend/api/agents/          # All AI agent implementations
- backend/api/                 # FastAPI server and tools
- frontend/src/                # React TypeScript frontend
- n8n_workflows/              # n8n workflow definitions for reference
- debug_orchestration.py       # Langfuse debugging utilities
```

**Essential Files to Read:**
- `backend/api/agents/main_agent.py` - Main orchestration agent
- `backend/api/agents/context_agent.py` - Context checking with JSON output
- `backend/api/agents/classifier.py` - Urgency classification agent  
- `backend/api/agents/contract_agent.py` - Contract search agent
- `backend/api/tools.py` - LangChain tool definitions
- `backend/api/main.py` - FastAPI server setup
- `debug_orchestration.py` - Trace analysis for debugging
- `frontend/src/components/ChatInterface.tsx` - Main chat UI

#### Step 3: Understand Current Debugging Process
**This system uses Langfuse for observability and debugging:**

- **Langfuse Dashboard**: Monitor agent orchestration traces
- **Debug Script**: Use `debug_orchestration.py` for detailed trace analysis
- **Key Metrics**: Agent orchestration success rate, tool calling patterns
- **Common Issues**: Agent initialization failures, tool availability problems

**Debugging Workflow (Logical Order):**
1. **Basic connectivity**: Verify API server running (`curl localhost:8000/`)
2. **Functional test**: Test agent orchestration (`tools/system/run_system.py --test`)
3. **IF issues found**: Analyze traces (`tools/debug/debug_orchestration.py`)
4. **Deep dive**: Focus on tool initialization and environment loading issues

#### Step 4: n8n Documentation Context
**Important**: This system was originally prototyped in n8n (LangChain JS) but is now implemented in Python. n8n workflows in this repo are for **reference only**.

**Key n8n Concepts That Apply:**
- **Tool calling architecture**: n8n's Tools Agent pattern influences our Python implementation
- **Agent orchestration**: Similar multi-agent workflow patterns
- **Memory management**: Session-based conversation continuity
- **Error handling**: Graceful degradation when tools fail

**n8n Documentation References:**
- Tool calling patterns: https://docs.n8n.io/advanced-ai/examples/understand-tools/
- Agent architecture: https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.agent/tools-agent/
- Workflow tools: https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.toolworkflow/

#### Step 5: Common Issues & Solutions
**Recent Problems Solved:**
- **Agent Initialization**: LLMs initialized at import time without environment variables
- **Tool Creation**: Tools created at module import vs runtime causing inconsistencies  
- **Missing Dependencies**: langchain-pinecone package missing from requirements
- **Output Parsing**: Incorrect JSON parsers on agents expecting plain text output

**Current Architecture Status:**
- ✅ Lazy loading implemented for all agents
- ✅ Runtime tool creation in `create_main_agent()`
- ✅ Proper error handling and graceful degradation
- ✅ Langfuse tracing active for debugging
- ✅ All dependencies in requirements.txt

#### Step 6: Development Environment Setup
**Before making changes (Docker-First Approach):**
1. **Check if Docker is already running**: `docker ps` (primary deployment method)
2. **If Docker running**: API server is on `localhost:8000`, skip to step 4
3. **If Docker not running**: Start with `docker-compose up -d` OR use `tools/system/run_system.py --backend` for development
4. Verify all environment variables loaded (OpenAI, Pinecone, Langfuse)
5. Check browser MCP tools available if needed

**Testing Approach (Docker-Aware Order):**
1. **Check current deployment**: `docker ps` (see if containers already running)
2. **Quick connectivity check**: `curl localhost:8000/` (verify backend responding)
3. **Comprehensive test**: `tools/system/run_system.py --test` (tests all agents + connectivity)
4. **IF problems found**: Use `tools/debug/debug_orchestration.py` for trace analysis
5. **IF still issues**: Manual `/main-agent` endpoint testing with specific queries

**Important**: This system primarily runs via Docker Compose. Always check `docker ps` first to avoid port conflicts when starting development servers.

#### Step 7: Change Log Management (IMPORTANT)
**Before making any significant changes:**
1. When you complete major fixes or implementations, ask the user: "Should I add these changes to the recent change logs?"
2. Document key changes in `RECENT_CHANGE_LOGS.md` for future AI assistants
3. Include: what was changed, why it was changed, and what the result was
4. Remove outdated/irrelevant changes as the log gets long

**Types of changes to log:**
- Bug fixes and their root causes
- New features or system enhancements
- Architecture changes or refactoring
- Environment or dependency updates
- Performance improvements or optimizations

#### Step 8: System Prompt Protection Protocol (CRITICAL)
**⚠️ NEVER modify agent system prompts without explicit permission:**

1. **System prompts are VERBATIM copies from n8n workflows** - they define the exact agent behavior and workflow logic
2. **Files containing system prompts:**
   - `backend/api/agents/main_agent.py` - Main orchestration workflow
   - `backend/api/agents/context_agent.py` - Context checking logic
   - `backend/api/agents/contract_agent.py` - Contract search behavior
   - `backend/api/agents/classifier.py` - Classification logic

3. **Before ANY changes to system prompts:**
   - **EXPLICITLY state** that you are proposing to modify a system prompt
   - **Explain WHY** the change is necessary
   - **REQUEST PERMISSION** from the user before proceeding
   - **Never include system prompt changes** in general code updates without calling them out

4. **System prompt changes can break:**
   - Agent orchestration workflow
   - n8n compatibility 
   - Expected agent behavior patterns
   - Integration between agents

**Example of correct approach:**
> "I need to modify the main agent's system prompt to fix the workflow issue. This will change how the agent processes requests. May I proceed with updating the system prompt in `main_agent.py`?"

**❌ Never do this:** Silently update system prompts as part of other changes

---

## 🚨 **Critical Recent Changes (Last 90 Days)**

<!--
WHAT THIS SECTION IS:
This section contains the most critical system changes that AI assistants need to understand immediately.
It provides quick context on recent enhancements, fixes, and warnings about things that would break the system.

REFRESH STRATEGY:
- Keep changes from last 90 days that are architecturally significant
- Archive minor bug fixes after 30 days
- Keep forever: Major architecture changes, system-breaking fixes, critical warnings
- Remove: Resolved minor issues, detailed debugging sessions, failed experiments
- Update quarterly: Move detailed histories to RECENT_CHANGE_LOGS.md
-->

### **Dual Memory Context Agent Enhancement (June 2025)**
- **What**: Context agent can now track partial user information across conversation turns, eliminating repetitive questioning
- **Key Enhancement**: Added dual memory access allowing context agent to see both user conversations AND agent summaries
- **Files**: `context_agent.py` (new `run_context_agent_with_dual_memory()`), `scoped_memory_manager.py`, `tools.py`
- **⚠️ Critical**: Don't modify original `run_context_agent()` function - needed for backward compatibility

### **Scoped Memory Architecture (January 2025)** 
- **What**: Complete memory system overhaul with isolated conversation channels per agent type
- **Key Enhancement**: Each agent has separate memory threads preventing cross-contamination
- **Files**: All agent files updated, new `memory/` directory with `ScopedMemoryManager`
- **⚠️ Critical**: Don't revert to old global memory dictionaries - causes memory leaks and conversation cross-contamination
- **Verification**: Run `test_scoped_memory_simple.py` to confirm isolation working

### **Docker Import Path Resolution (June 2025)**
- **What**: Fixed fundamental module import failures in Docker containers
- **Key Fix**: Changed all imports from `api.module` to `module` format for container compatibility
- **Files**: All agent files (`main_agent.py`, `context_agent.py`, `contract_agent.py`, `classifier.py`), `database.py`
- **⚠️ Critical**: Don't revert import paths to `api.` prefix - will break Docker container startup
- **Verification**: `docker-compose up` should start cleanly without import errors

**📚 Full Change History**: See `RECENT_CHANGE_LOGS.md` for complete implementation details and testing evidence.

---

### Table of Contents
1. [Product Overview](#product-overview)
2. [System Architecture](#system-architecture)
3. [Core Components](#core-components)
4. [Agent System Detailed Breakdown](#agent-system-detailed-breakdown)
5. [Data Flow and Workflow](#data-flow-and-workflow)
6. [Technology Stack](#technology-stack)
7. [API Endpoints](#api-endpoints)
8. [Database Schema](#database-schema)
9. [Frontend Architecture](#frontend-architecture)
10. [Infrastructure and Deployment](#infrastructure-and-deployment)
11. [Integration with n8n](#integration-with-n8n)
12. [Key Design Decisions](#key-design-decisions)
13. [Development Guidelines](#development-guidelines)

---

## 1. Product Overview

**Abodient** is an AI-powered property management support system that acts as an intelligent intermediary between tenants and landlords. The system uses multiple specialized AI agents to:

- **Understand and classify** tenant issues by urgency and responsibility
- **Gather necessary context** through intelligent questioning
- **Check contractual obligations** using vector search through rental agreements
- **Provide automated responses** and action recommendations
- **Maintain conversation history** for continuous support

The core value proposition is automating routine tenant-landlord communications while ensuring legal compliance and proper issue resolution.

## 2. System Architecture

The system follows a microservices architecture with these main components:

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   API Server │────▶│  AI Agents      │
│  (React/TS)     │     │  (FastAPI)   │     │  (LangChain)    │
└─────────────────┘     └──────────────┘     └─────────────────┘
                               │                      │
                               ▼                      ▼
                        ┌──────────────┐     ┌─────────────────┐
                        │  PostgreSQL  │     │    Pinecone     │
                        │              │     │ (Vector Store)  │
                        └──────────────┘     └─────────────────┘
```

### Key Architecture Decisions:
- **Separation of Concerns**: Each agent handles a specific domain (context, classification, contracts)
- **Scoped Memory Architecture**: Each agent has isolated memory channels preventing cross-contamination
- **Memory Channel Isolation**: User conversations and agent-to-agent conversations are completely separate
- **Vector Search**: Pinecone enables semantic search through contracts and classification data
- **Session Management**: Each conversation has a unique session ID with isolated memory across all channels
- **n8n Architecture Compliance**: Memory scoping matches n8n conversation patterns exactly

## 3. Core Components

### 3.1 Backend API (`backend/api/`)
- **FastAPI server** with CORS support for frontend integration
- **API Key authentication** for security
- **Database integration** using SQLAlchemy ORM
- **OpenTelemetry** instrumentation for observability
- **Scoped Memory Management** with isolated conversation channels

### 3.2 Agent System (`backend/api/agents/`)
Four specialized agents work together with scoped memory isolation:
1. **Context Agent**: Ensures queries have sufficient detail (isolated memory channel)
2. **Classifier Agent**: Determines urgency and responsibility (isolated memory channel)
3. **Contract Agent**: Searches rental agreements for relevant clauses (isolated memory channel)
4. **Main Agent**: Orchestrates the workflow and generates responses (user conversation memory)

### 3.3 Memory System (`backend/api/memory/`)
- **ScopedMemoryManager**: Centralized memory management with conversation channel isolation
- **Memory Channels**: Separate channels for user conversations and agent-to-agent communications
- **Session Management**: Activity tracking and statistics for session lifecycle management
- **n8n Architecture Compliance**: Matches n8n conversation scoping patterns exactly

### 3.3 Frontend (`frontend/`)
- **React with TypeScript** for type safety
- **Tailwind CSS** for styling
- **React Router** for navigation
- **React Query** for data fetching
- Multiple pages including Chat, Tasks, Calendar, Reports, etc.

### 3.4 Infrastructure
- **Docker Compose** for local development
- **PostgreSQL** for persistent storage
- **Redis** for caching/queuing
- **n8n** integration for workflow automation

## 4. Agent System Detailed Breakdown

### 4.1 Main Agent (`main_agent.py`)
**Purpose**: Orchestrates the entire conversation flow

**Key Features**:
- Uses LangChain's OpenAI Tools Agent
- Maintains user conversation memory (window: 10 messages)
- Follows a strict 5-step workflow
- Temperature: 0.7 (balanced creativity)
- **Scoped Memory**: Uses dedicated user memory channel, isolated from agent-to-agent communications

**Workflow**:
```python
1. Context Check → Always first, no exceptions
2. Query Simplification → Convert to vector search terms
3. Contract Search → Check legal obligations
4. Classification → Determine urgency/responsibility
5. Response Generation → Synthesize all information
```

### 4.2 Context Agent (`context_agent.py`)
**Purpose**: Ensures complete information gathering

**Key Features**:
- Structured JSON output using Pydantic models
- Checks for the "5 W's": What, Where, When, How, Prior Attempts
- Temperature: 0.3 (more deterministic)
- **Scoped Memory**: Uses isolated memory channel for Main Agent ↔ Context Agent conversations
- **Fixed Memory Integration**: Now properly includes conversation history in prompts

**Response Structure**:
```json
{
  "is_clear": true/false,
  "is_relevant": true/false,
  "requires_clarification": true/false,
  "clarifying_question": "string",
  "requires_context": true/false,
  "additional_context_question": "string",
  "query_summary": "string"
}
```

### 4.3 Classifier Agent (`classifier.py`)
**Purpose**: Determines issue urgency and responsibility assignment

**Key Features**:
- Vector search in Pinecone "urgency-search" index
- Namespace: "urgency-1"
- Returns urgency levels and responsibility assignments
- Temperature: 0 (fully deterministic)
- **Scoped Memory**: Uses isolated memory channel for Main Agent ↔ Classifier Agent conversations

**Classification Categories**:
- **Urgent**: Health/safety risks, habitability issues
- **High Priority**: Major repairs, structural issues
- **Medium Priority**: Minor repairs, convenience issues
- **Low Priority**: Cosmetic issues, permission requests

### 4.4 Contract Agent (`contract_agent.py`)
**Purpose**: Searches rental agreements for relevant clauses

**Key Features**:
- Vector search in Pinecone "contract-search" index
- Namespace: "contract-1"
- Returns specific contract sections
- Temperature: 0 (fully deterministic)
- **Scoped Memory**: Uses isolated memory channel for Main Agent ↔ Contract Agent conversations

## 5. Data Flow and Workflow

### 5.1 Request Flow
```
1. User sends message via Chat UI
2. Frontend calls POST /main-agent with session_id and text
3. API stores user message in PostgreSQL
4. Main Agent workflow begins:
   a. Context Agent analyzes completeness
   b. Query converted to search terms
   c. Contract Agent searches agreements
   d. Classifier Agent determines urgency
   e. Response generated
5. AI response stored in PostgreSQL
6. Response sent back to frontend
7. UI updates with new message
```

### 5.2 Memory Management (Updated: Scoped Memory Architecture)
- **Scoped Memory Manager**: Unified memory management with isolated conversation channels
- **Memory Isolation**: Each agent has separate memory for its conversation thread with main agent
- **User Memory**: User ↔ Main Agent conversations (window: 10 messages)
- **Agent Memory**: Main Agent ↔ Specialist Agent conversations (window: 5 messages each)
- **Session-based**: Each session_id has isolated memory across all channels
- **Persistence**: Chat history stored in PostgreSQL
- **Activity Tracking**: Session activity tracked for cleanup management

**Memory Channel Structure**:
```python
# Get memory for different conversation types
user_memory = get_user_memory(session_id)                    # User ↔ Main Agent
context_memory = get_agent_memory(session_id, "context")     # Main ↔ Context Agent  
contract_memory = get_agent_memory(session_id, "contract")   # Main ↔ Contract Agent
classifier_memory = get_agent_memory(session_id, "classifier") # Main ↔ Classifier Agent
```

**Key Benefits**:
- **Perfect Isolation**: User conversations never contaminate agent-to-agent conversations
- **Session Separation**: Different users maintain completely separate memories
- **n8n Architecture Match**: Replicates n8n conversation scoping behavior exactly
- **Scalable**: Activity tracking enables future session cleanup implementation

## 6. Technology Stack

### Backend
- **Python 3.x** - Primary backend language
- **FastAPI** - High-performance web framework
- **LangChain** - LLM application framework
- **LangChain-OpenAI** - OpenAI integration
- **Pinecone** - Vector database for semantic search
- **SQLAlchemy** - SQL toolkit and ORM
- **PostgreSQL** - Primary database
- **Redis** - Caching and queuing
- **Langfuse** - LLM observability
- **OpenTelemetry** - Distributed tracing
- **ScopedMemoryManager** - Custom memory isolation system for conversation channels

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Utility-first CSS
- **shadcn/ui** - Component library
- **React Query** - Data fetching
- **React Router** - Navigation

### Infrastructure
- **Docker & Docker Compose** - Containerization
- **n8n** - Workflow automation (external integration) - was used to build the original workflow and agent orchestration, is only used in this codebase for reference and for checking similarity of functionality.

## 7. API Endpoints

### 7.1 Main Endpoints

#### `POST /main-agent`
**Purpose**: Main conversation endpoint
```json
Request:
{
  "session_id": "string",
  "text": "string"
}

Response:
{
  "chat_output": "AI response text",
  "query_summary": "Summary of query",
  "actions": ["List of actions"]
}
```

#### `POST /classify`
**Purpose**: Classify urgency and responsibility
```json
Request:
{
  "session_id": "string",
  "text": "string"
}

Response: "Classification summary paragraph"
```

#### `POST /context`
**Purpose**: Check if more context needed
```json
Request:
{
  "session_id": "string", 
  "text": "string"
}

Response:
{
  "is_clear": boolean,
  "is_relevant": boolean,
  "requires_clarification": boolean,
  "clarifying_question": "string",
  "requires_context": boolean,
  "additional_context_question": "string",
  "query_summary": "string"
}
```

#### `POST /contract`
**Purpose**: Search contract information
```json
Request:
{
  "session_id": "string",
  "text": "string"
}

Response: "Contract analysis text"
```

#### `GET /chat-history/{session_id}`
**Purpose**: Retrieve conversation history
```json
Response:
[
  {
    "sender": "user|ai",
    "message": "string",
    "timestamp": "datetime"
  }
]
```

### 7.2 Authentication
All endpoints require `X-API-KEY` header matching environment variable `API_KEY`.

## 8. Database Schema

### 8.1 Tables

#### `conversation_messages`
Stores all chat messages
```sql
- id: String (Primary Key)
- session_id: String (Indexed)
- sender: String ('user' or 'ai')
- message: Text
- timestamp: DateTime
```

#### `session_memory`
Stores serialized memory for each session
```sql
- session_id: String (Primary Key)
- memory_json: Text (JSON string)
```

## 9. Frontend Architecture

### 9.1 Page Structure
- **ActionsPage** (`/`) - Main dashboard
- **TasksPage** (`/tasks`) - Task management
- **ContactsPage** (`/contacts`) - Contact directory
- **CalendarPage** (`/calendar`) - Calendar view
- **ReportsPage** (`/reports`) - Analytics/reports
- **DatabasePage** (`/database`) - Knowledge base
- **ChatPage** (`/chat`) - Tenant support chat
- **ConfigurationPage** (`/configuration`) - System settings

### 9.2 Chat Interface (`ChatInterface.tsx`)
**Key Features**:
- Real-time message display
- Loading states with spinner
- Error handling
- Session-based conversations
- Responsive design with Tailwind

**State Management**:
```typescript
- messages: Message[] - All chat messages
- inputText: string - Current input
- loading: boolean - API call status
```

## 10. Infrastructure and Deployment

### 10.1 Docker Services
```yaml
services:
  frontend:    # React app on port 8080
  api:         # FastAPI server on port 8000
  worker:      # Background worker (placeholder)
  redis:       # Redis cache
  postgres:    # PostgreSQL database
```

### 10.2 Environment Variables
Key variables needed:
- `API_KEY` - API authentication
- `DATABASE_URL` - PostgreSQL connection
- `PINECONE_API_KEY` - Vector search
- `OPENAI_API_KEY` - LLM access
- `VITE_API_URL` - Frontend API endpoint
- `VITE_API_KEY` - Frontend API key

## 11. Integration with n8n

The system includes n8n workflow definitions for:
- **classifierAgent (3).json** - Classification workflow
- **contractAgent (2).json** - Contract search workflow
- **contextAgent.json** - Context checking workflow
- **NEW_main_agent.json** - Main orchestration workflow

These workflows can be imported into n8n for visual workflow management and execution.

## 12. Key Design Decisions

### 12.1 Agent Separation
**Why**: Each agent has a specific responsibility, making the system modular and maintainable. Changes to classification logic don't affect contract searching.

### 12.2 Shared Memory Architecture
**Why**: Ensures all agents have access to conversation context without passing large payloads between services.

### 12.3 Vector Search for Knowledge
**Why**: Semantic search provides better results than keyword matching for natural language queries about contracts and classifications.

### 12.4 Structured JSON Responses
**Why**: Predictable output format makes frontend integration reliable and enables better error handling.

### 12.5 Session-Based Isolation
**Why**: Prevents conversation cross-contamination and enables concurrent users.

## 13. Development Guidelines

### 13.1 Adding New Agents
1. Create new agent file in `backend/api/agents/`
2. Implement with `@observe` decorator for tracing
3. Add corresponding tool in `tools.py`
4. Update main agent's system prompt
5. Add to main agent's tool list

### 13.2 Modifying Workflows
1. Update system prompts carefully - they control behavior
2. Test with various edge cases
3. Monitor token usage (window size affects costs)
4. Update both Python code and n8n workflows if applicable

### 13.3 Frontend Development
1. Use TypeScript for all new components
2. Follow existing Tailwind patterns
3. Handle loading and error states
4. Test responsive design

### 13.4 Testing Considerations
- **Memory Isolation Testing**: Verify scoped memory works correctly with comprehensive test suite
- **Agent Integration Testing**: Test agent interactions with mock responses
- **Session Isolation**: Verify session isolation across memory channels
- **Vector Search**: Check vector search relevance
- **JSON Structures**: Validate JSON response structures
- **Error Handling**: Test error handling paths
- **Memory Channel Testing**: Ensure user and agent conversations remain isolated

### 13.5 Running Tests
**Comprehensive Test Suite** (recommended):
```bash
cd backend
python -m pytest tests/ -v
```

**Quick Test Script** (no pytest dependency):
```bash
cd backend
python test_scoped_memory_simple.py
```

**Agent Integration Test**:
```bash
cd backend
python test_agent_integration.py
```

**Test Coverage**:
- 19 unit tests for ScopedMemoryManager functionality
- 4 integration tests with real agents
- Memory isolation verification
- n8n conversation scoping compliance
- Session activity tracking
- All tests passing (23/23 total)

---

This documentation provides a comprehensive understanding of the Abodient codebase. Any LLM reading this should have sufficient context to:
- Understand the system's purpose and architecture
- Make informed decisions about modifications
- Add new features while maintaining consistency
- Debug issues effectively
- Optimize performance

The system is designed to be extensible, with clear separation of concerns and modular architecture that allows for future enhancements while maintaining the core tenant support functionality. 
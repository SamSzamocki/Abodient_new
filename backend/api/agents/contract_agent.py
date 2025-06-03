import os, json
from pinecone import Pinecone
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import HumanMessage, SystemMessage
from langchain_pinecone import PineconeVectorStore
from langfuse.decorators import observe

# Change from import-time initialization to lazy loading
_llm = None
_pinecone_client = None
_pinecone_index = None
_embedder = None
_vectorstore = None

def get_llm():
    """Lazy-load the LLM to ensure environment variables are available"""
    global _llm
    if _llm is None:
        # gpt-4o-mini should always be the default model for all agents
        _llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.3)
    return _llm

def get_pinecone_components():
    """Lazy-load Pinecone components to ensure environment variables are available"""
    global _pinecone_client, _pinecone_index, _embedder, _vectorstore
    
    if _pinecone_client is None:
        _pinecone_client = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        _pinecone_index = _pinecone_client.Index("contract-search")  # Matches n8n pineconeIndex exactly
        _embedder = OpenAIEmbeddings(model="text-embedding-3-small")
        _vectorstore = PineconeVectorStore(index=_pinecone_index, embedding=_embedder)
    
    return _pinecone_client, _pinecone_index, _embedder, _vectorstore

# Shared memory storage - matches n8n's shared session key
session_memories = {}

def get_shared_memory(session_id: str = "187a3d5d3eb44c06b2e3154710ca2ae7") -> ConversationBufferWindowMemory:
    """
    Get shared memory - matches n8n's Window Buffer Memory configuration
    Uses "Take from previous node automatically" behavior from n8n
    """
    if session_id not in session_memories:
        session_memories[session_id] = ConversationBufferWindowMemory(
            k=5,  # Window size - matches n8n default
            memory_key="chat_history",
            return_messages=True
        )
    return session_memories[session_id]

# EXACT system prompt from n8n contractAgent (2).json
SYSTEM_PROMPT = """You are an expert in analysing tenancy contracts to help answer user queries. 

Available tool
-contractInformation

Instructions
Use contractInformation tool to find relevant contractual information related to the query. 

Tasks
1) understand the intent of the query and 2) subsequently turn this into an efficient vector search query which you must pass to contractInformation tool

Output
Your response to a query must include the full contractual position, clear stating the relevant section of the contract, and provide as much relevant information as you can to help answer the query.

Your tone must be helpful, clear and friendly"""

@observe(name="contract_agent")
def run_contract_agent(query: str, session_id: str = "187a3d5d3eb44c06b2e3154710ca2ae7") -> str:
    """
    Contract agent that matches n8n contractAgent (2).json structure exactly
    """
    print(f"[CONTRACT AGENT] Processing query: {query}")
    
    # Get shared memory
    memory = get_shared_memory(session_id)
    
    try:
        # Vector search - matches n8n's Vector Store Tool configuration exactly
        pinecone_client, pinecone_index, embedder, vectorstore = get_pinecone_components()
        embedding = embedder.embed_query(query)
        results = pinecone_index.query(
            vector=embedding, 
            top_k=10,  # Matches n8n topK: 10
            include_metadata=True, 
            namespace="contract-1"  # Matches n8n pineconeNamespace exactly
        )
        
        # Extract contract snippets
        snippets = "\n".join(match["metadata"]["text"] for match in results["matches"])
        print(f"[CONTRACT AGENT] Found {len(results['matches'])} contract matches")
        
        # Build messages with memory context
        messages = [SystemMessage(content=SYSTEM_PROMPT)]
        
        # Add conversation history from memory
        try:
            memory_vars = memory.load_memory_variables({})
            if "chat_history" in memory_vars and memory_vars["chat_history"]:
                messages.extend(memory_vars["chat_history"])
        except Exception as e:
            print(f"[CONTRACT AGENT] Memory load error: {e}")
        
        # Add current query with contract information
        query_with_context = f"Query: {query}\ncontractInformation tool results:\n{snippets}"
        messages.append(HumanMessage(content=query_with_context))
        
        # Generate response using lazy-loaded LLM
        llm = get_llm()
        response = llm.invoke(messages)
        
        # Add to memory
        memory.chat_memory.add_user_message(query)
        memory.chat_memory.add_ai_message(response.content)
        
        print(f"[CONTRACT AGENT] Generated response")
        return response.content
        
    except Exception as e:
        print(f"[CONTRACT AGENT] Error: {e}")
        return f"I apologize, but I encountered an error while analyzing the contract: {str(e)}"

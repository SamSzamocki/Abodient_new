import os, json
from pinecone import Pinecone
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import HumanMessage, SystemMessage
from langchain_pinecone import PineconeVectorStore
from langfuse.decorators import observe

# LLM configuration matching n8n
llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

# Shared memory storage - matches n8n's shared session key
session_memories = {}

def get_shared_memory(session_id: str = "187a3d5d3eb44c06b2e3154710ca2ae7") -> ConversationBufferWindowMemory:
    """
    Get shared memory - matches n8n's Window Buffer Memory configuration
    """
    if session_id not in session_memories:
        session_memories[session_id] = ConversationBufferWindowMemory(
            k=5,  # Window size
            memory_key="chat_history",
            return_messages=True
        )
    return session_memories[session_id]

# EXACT system prompt from n8n classifierAgent (3).json
SYSTEM_PROMPT = """You are an expert in providing a helpful assessment of the urgency and general responsibility of issues raised by tenants about their tenancy.  


***Available tool
-classifierInformation

***Instructions
Use the classifierInformation tool to determine the urgency and responsibilities related to the type of issue raised

***Tasks
1) understand the intent of the query based on the conversation history and 2) subsequently turn this into an efficient vector search query which you must pass to classifierInformation tool

***Output
1 short paragraph summarising the key information. The summary should describe the situation and high level details around urgency and responsibility

***Important
NEVER recommend the tenant reach out or report an issue to the landlord

Your tone must be helpful, clear and friendly"""

# Pinecone configuration matching n8n
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("urgency-search")
embedder = OpenAIEmbeddings(model="text-embedding-3-small")

# Initialize embeddings and vector store
vectorstore = PineconeVectorStore(index=index, embedding=embedder)

@observe(name="classifier_agent")
def run_classifier_agent(query: str, session_id: str = "187a3d5d3eb44c06b2e3154710ca2ae7") -> str:
    """
    Classifier agent that matches n8n classifierAgent (3).json structure
    """
    print(f"[CLASSIFIER AGENT] Processing query: {query}")
    
    # Get shared memory
    memory = get_shared_memory(session_id)
    
    try:
        # Vector search - matches n8n's Vector Store Tool configuration
        embedding = embedder.embed_query(query)
        results = index.query(
            vector=embedding, 
            top_k=10,  # Matches n8n topK: 10
            include_metadata=True, 
            namespace="urgency-1"  # Matches n8n pineconeNamespace
        )
        
        # Extract classification snippets
        snippets = "\n".join(match["metadata"]["text"] for match in results["matches"])
        print(f"[CLASSIFIER AGENT] Found {len(results['matches'])} classification matches")
        
        # Build messages with memory context
        messages = [SystemMessage(content=SYSTEM_PROMPT)]
        
        # Add conversation history from memory
        try:
            memory_vars = memory.load_memory_variables({})
            if "chat_history" in memory_vars and memory_vars["chat_history"]:
                messages.extend(memory_vars["chat_history"])
        except Exception as e:
            print(f"[CLASSIFIER AGENT] Memory load error: {e}")
        
        # Add current query with classification information
        query_with_context = f"Query: {query}\nclassifierInformation tool results:\n{snippets}"
        messages.append(HumanMessage(content=query_with_context))
        
        # Generate response
        response = llm.invoke(messages)
        
        # Add to memory
        memory.chat_memory.add_user_message(query)
        memory.chat_memory.add_ai_message(response.content)
        
        print(f"[CLASSIFIER AGENT] Generated response")
        return response.content
        
    except Exception as e:
        print(f"[CLASSIFIER AGENT] Error: {str(e)}")
        return "I apologize, but I encountered an error while classifying your request. Please try rephrasing your question."

# Legacy function names for backwards compatibility
def classify(query: str) -> str:
    """Legacy function name - redirects to run_classifier_agent"""
    return run_classifier_agent(query)


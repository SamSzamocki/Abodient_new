import os, json
from pinecone import Pinecone
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.memory import ConversationBufferMemory
from langfuse.callback import CallbackHandler

# --- System prompt ---
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

# --- Initialise models ---
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("contract-search")

embedder = OpenAIEmbeddings(model="text-embedding-3-small")
llm = ChatOpenAI(model_name="gpt-4o-mini")

# Add your Langfuse handler (use your latest keys)
langfuse_handler = CallbackHandler(
    public_key="pk-lf-d9a88b84-cdab-44eb-bada-98f2c8567ab7",
    secret_key="sk-lf-06a5516a-d683-44d4-b2b2-418ad43429f3",
    host="https://cloud.langfuse.com"
)

session_memories = {}

# --- Main search + LLM interpretation function ---
def search_contract(query: str) -> str:
    """
    Given a user query, return a detailed response about what the contract says.
    """
    try:
        embedding = embedder.embed_query(query)
        results = index.query(
            vector=embedding,
            top_k=10,  # Match n8n's top_k setting
            include_metadata=True,
            namespace="contract-1"
        )
        snippets = "\n".join(match["metadata"]["text"] for match in results["matches"])

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Search query: {query}\nContract snippets:\n{snippets}")
        ]

        # Add Langfuse tracing to the LLM call
        reply = llm.invoke(messages, config={"callbacks": [langfuse_handler]})
        return reply.content

    except Exception as e:
        return "I apologize, but I encountered an error while searching the contract. Please try rephrasing your question."

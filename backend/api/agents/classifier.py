import os, json
from pinecone import Pinecone
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.schema import HumanMessage, SystemMessage
from langchain.memory import ConversationBufferMemory
from langfuse.callback import CallbackHandler

# 1. Initialise Pinecone v3 client
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("urgency-search")

# 2. Prepare models
embedder = OpenAIEmbeddings(model="text-embedding-3-small")
llm = ChatOpenAI(model_name="gpt-4o-mini")      # inexpensive GPT-4 tier

langfuse_handler = CallbackHandler(
    public_key="pk-lf-d9a88b84-cdab-44eb-bada-98f2c8567ab7",
    secret_key="sk-lf-06a5516a-d683-44d4-b2b2-418ad43429f3",
    host="https://cloud.langfuse.com"
)

SYSTEM_PROMPT = """You are an expert in providing a helpful assessment of the urgency and general responsibility of issues raised by tenants about their tenancy.  

***Available tool
-classifierInformation

***Instructions
Use the classifierInformation tool to determine the urgency and responsibilities related to the type of issue raised

***Tasks
1) understand the intent of the query based on the conversation history and 
2) subsequently turn this into an efficient vector search query which you must pass to classifierInformation tool

***Output
1 short paragraph summarising the key information. The summary should describe the situation and high level details around urgency and responsibility

***Important
NEVER recommend the tenant reach out or report an issue to the landlord

Your tone must be helpful, clear and friendly"""

session_memories = {}

def classify(text: str) -> str:
    """Return a summary paragraph about urgency & responsibility for a tenant message."""
    try:
        # -- fetch similar past cases from vector store
        embedding = embedder.embed_query(text)
        matches = index.query(
            vector=embedding,
            top_k=3,
            include_metadata=True,
            namespace="urgency-1"
        )   
        print("Pinecone matches:", matches)

        snippets = "\n".join(m["metadata"]["text"] for m in matches["matches"])

        # -- ask the LLM
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Tenant text: {text}\nSimilar cases:\n{snippets}"),
        ]
        reply = llm.invoke(messages, config={"callbacks": [langfuse_handler]})
        return reply.content

    except Exception as e:
        return f"Sorry, something went wrong while processing your request. (Error: {str(e)})"


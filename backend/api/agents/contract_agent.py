import os, json
from pinecone import Pinecone
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

# --- System prompt ---
SYSTEM_PROMPT = """
You are an expert assistant that helps interpret tenancy agreements.

Your job is to assess whether a user’s issue is covered by the landlord’s responsibilities under their rental contract. You will be given a search query and a set of relevant snippets pulled from the tenancy agreement or policy documents.

Use these to determine what the contract says. If nothing matches, return "unknown".

Return JSON in this format:
{
  "responsibility": "landlord|tenant|unclear",
  "summary": "Brief explanation of what the contract says or why it’s unclear"
}

Keep your summary short, direct, and based only on the snippets provided.
"""

# --- Initialise models ---
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("contract-search")

embedder = OpenAIEmbeddings(model="text-embedding-3-small")
llm = ChatOpenAI(model_name="gpt-4o-mini")

# --- Main search + LLM interpretation function ---
def search_contract(query: str) -> dict:
    """
    Given a user query, return a structured summary of what the contract says.
    """
    try:
        embedding = embedder.embed_query(query)
        results = index.query(
            vector=embedding,
            top_k=5,
            include_metadata=True,
            namespace="contract-1"
        )
        snippets = "\n".join(match["metadata"]["text"] for match in results["matches"])

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Search query: {query}\nContract snippets:\n{snippets}")
        ]

        reply = llm(messages).content
        return json.loads(reply)

    except Exception as e:
        return {"error": str(e)}

from langchain_openai import ChatOpenAI
from langfuse.callback import CallbackHandler

# Use your new Langfuse keys here
langfuse_handler = CallbackHandler(
    public_key="pk-lf-d9a88b84-cdab-44eb-bada-98f2c8567ab7",
    secret_key="sk-lf-06a5516a-d683-44d4-b2b2-418ad43429f3",
    host="https://cloud.langfuse.com"
)

llm = ChatOpenAI(model_name="gpt-4o-mini")  # or "gpt-4o" if you have access

prompt = "Say hello from Langfuse test!"

print("Sending prompt to LLM with Langfuse callback...")
response = llm.invoke(prompt, config={"callbacks": [langfuse_handler]})
print("LLM response:", response)

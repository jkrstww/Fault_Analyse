from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
import json

query = "What is 3 * 12? Also, what is 11 + 49?"

messages = [HumanMessage(query)]

llm = ChatOllama(
    model="llama3.2"
)

@tool
def add(a: int, b: int) -> int:
    """Adds a and b."""
    return a + b

@tool
def multiply(a: int, b: int) -> int:
    """Multiplies a and b."""
    return a * b

tools = [add, multiply]

llm_with_tools = llm.bind_tools(tools)

ai_msg = llm_with_tools.invoke(messages)

print(ai_msg.tool_calls)

messages.append(ai_msg)

print(json.dumps(ai_msg.__dict__, indent=2))

import asyncio
import os
from typing import Annotated, List, TypedDict, Union

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

# Load environment variables
load_dotenv()

# --- LOCAL TOOLS (NO MCP) ---

@tool
def add(a: float, b: float) -> float:
    """Add two numbers."""
    print(f"[*] Local Tool 'add' called with: {a}, {b}")
    return a + b

@tool
def subtract(a: float, b: float) -> float:
    """Subtract b from a."""
    print(f"[*] Local Tool 'subtract' called with: {a}, {b}")
    return a - b

@tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    print(f"[*] Local Tool 'multiply' called with: {a}, {b}")
    return a * b

@tool
def divide(a: float, b: float) -> float:
    """Divide a by b. Raises error if b is zero."""
    print(f"[*] Local Tool 'divide' called with: {a}, {b}")
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

# --- LANGGRAPH AGENT ---

class AgentState(TypedDict):
    """The state of the graph."""
    messages: Annotated[List[BaseMessage], lambda x, y: x + y]

class LocalMathAgent:
    """
    Orchestrated LangGraph agent using LOCAL tools.
    Exact same graph logic as the MCP version, but without the network overhead.
    """
    def __init__(self):
        self.tools = [add, subtract, multiply, divide]
        self.graph = self._build_graph()

    def _build_graph(self):
        # Using the same model and sequential constraint
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools(
            self.tools, 
            parallel_tool_calls=False
        )

        def call_model(state: AgentState):
            system_instruction = (
                "You are a helpful mathematical assistant. "
                "IMPORTANT: You must perform calculations STEP-BY-STEP. "
                "Wait for the result of one tool call before starting the next."
            )
            messages = [("system", system_instruction)] + state["messages"]
            response = llm.invoke(messages)
            return {"messages": [response]}

        def should_continue(state: AgentState):
            last_message = state["messages"][-1]
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                return "tools"
            return END

        workflow = StateGraph(AgentState)
        workflow.add_node("agent", call_model)
        workflow.add_node("tools", ToolNode(self.tools))
        workflow.set_entry_point("agent")
        workflow.add_conditional_edges("agent", should_continue)
        workflow.add_edge("tools", "agent")
        return workflow.compile()

    async def chat(self, user_input: str):
        inputs = {"messages": [HumanMessage(content=user_input)]}
        async for output in self.graph.astream(inputs, stream_mode="values"):
            message = output["messages"][-1]
            
            # Skip interim messages/tool calls in output
            is_tool_call = hasattr(message, "tool_calls") and message.tool_calls
            if not is_tool_call and not isinstance(message, ToolMessage) and message.content:
                if message != inputs["messages"][0]: 
                    print(f"\nAgent Output: {message.content}")

# --- MAIN EXECUTION ---

async def main():
    agent = LocalMathAgent()
    
    print("\n" + "="*50)
    print("LOCAL MATH AGENT (WITHOUT MCP)")
    print("="*50)

    while True:
        query = input("\nWhat is your calculation? (or 'exit'): ")
        if query.lower() in ["exit", "quit"]:
            break

        print(f"[*] Thinking...")
        await agent.chat(query)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGoodbye!")

import asyncio
import os
from typing import Annotated, List, TypedDict, Union, Optional, Any, Dict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from pydantic import create_model, Field, BaseModel

# Import refactored components
from client import RegistryRouter, MCPConnection

# Load environment variables
load_dotenv()

# --- DYNAMIC DISPATCHER ---

class MCPDynamicTool(BaseTool):
    """
    A Class-based Dynamic Dispatcher for MCP Tools.
    Handles its own schema mapping and execution logic.
    """
    mcp_tool_name: str
    mcp_session: Any

    @classmethod
    def from_mcp_metadata(cls, metadata: Any, session: Any):
        """Builds a Tool instance directly from MCP metadata."""
        # 1. Map JSON Schema types to Python types
        type_map = {"number": float, "string": str, "integer": int, "boolean": bool}
        
        # 2. Build the field definitions for pydantic.create_model
        fields = {}
        if "properties" in metadata.inputSchema:
            for param_name, specs in metadata.inputSchema["properties"].items():
                py_type = type_map.get(specs.get("type"), str)
                description = specs.get("description", "")
                
                required = metadata.inputSchema.get("required", [])
                if param_name in required:
                    fields[param_name] = (py_type, Field(..., description=description))
                else:
                    fields[param_name] = (py_type, Field(None, description=description))

        # 3. Create the dynamic Pydantic model for validation
        args_schema = create_model(f"{metadata.name}_input", **fields)
        
        return cls(
            name=metadata.name,
            description=metadata.description,
            args_schema=args_schema,
            mcp_tool_name=metadata.name,
            mcp_session=session
        )

    async def _arun(self, **kwargs: Any) -> str:
        """Dynamic async execution of the tool via MCP."""
        print(f"[*] Dispatching to MCP Tool '{self.mcp_tool_name}' with args: {kwargs}")
        result = await self.mcp_session.call_tool(self.mcp_tool_name, kwargs)
        res_text = str(result.content[0].text)
        print(f"[*] Tool '{self.mcp_tool_name}' returned: {res_text}")
        return res_text

    def _run(self, **kwargs: Any) -> str:
        """Sync execution - not supported for MCP."""
        raise NotImplementedError("MCP tools require async execution.")

# --- LANGGRAPH AGENT ---

class AgentState(TypedDict):
    """The state of the graph."""
    messages: Annotated[List[BaseMessage], lambda x, y: x + y]

class UniversalMCPAgent:
    """Orchestrated LangGraph agent that works with any routed MCP session."""
    def __init__(self, mcp_session, system_instruction: str, tools_metadata):
        self.mcp_session = mcp_session
        self.system_instruction = system_instruction
        self.tools = self._build_tools(tools_metadata)
        self.graph = self._build_graph()

    def _build_tools(self, tools_metadata):
        """Cleanly constructs tools using the Dynamic Dispatcher Class."""
        data = [
            MCPDynamicTool.from_mcp_metadata(t, self.mcp_session) 
            for t in tools_metadata
        ]
        print(f"[*] tools_meta   = {data} \n")
        return data

    def _build_graph(self):
        # Force sequential execution by disabling parallel tool calls
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools(
            self.tools, 
            parallel_tool_calls=False
        )

        def call_model(state: AgentState):
            messages = [("system", self.system_instruction)] + state["messages"]
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
            
            # Message check: Skip messages without content or those that are interim tool calls
            is_tool_call = hasattr(message, "tool_calls") and message.tool_calls
            if not is_tool_call and not isinstance(message, ToolMessage) and message.content:
                if message != inputs["messages"][0]: 
                    print(f"\nAgent Output: {message.content}")

# --- MAIN EXECUTION ---

async def main():
    router = RegistryRouter("servers.json")
    
    print("\n" + "="*50)
    print("SCALABLE MCP ROUTING AGENT")
    print("="*50)

    while True:
        query = input("\nWhat is your request? (or 'exit'): ")
        if query.lower() in ["exit", "quit"]:
            break

        print(f"[*] Routing query to registry...")
        target_server = await router.route_query(query)
        
        if not target_server:
            print("[!] Router: No suitable server found in registry for this task.")
            continue
            
        print(f"[*] Router selected: {target_server['name']} ({target_server['url']})")

        try:
            async with MCPConnection(target_server["url"]) as mcp:
                tools_meta, instruction = await mcp.get_tools_and_instructions()
                
                print(f"[*] Initializing Dynamic Agent for session...")
                agent = UniversalMCPAgent(mcp.session, instruction, tools_meta)
                
                await agent.chat(query)
                
        except Exception as e:
            print(f"\n[!] Final Result: Could not complete task because the selected server is currently unreachable.")
            print(f"    (Error: {e})")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGoodbye!")

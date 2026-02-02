import asyncio
import json
from typing import Optional, List
from contextlib import AsyncExitStack
from mcp import ClientSession
from mcp.client.sse import sse_client
from langchain_openai import ChatOpenAI

class RegistryRouter:
    """Manages server discovery and routing logic."""
    def __init__(self, registry_path: str):
        with open(registry_path, "r") as f:
            self.servers = json.load(f)
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    async def route_query(self, query: str) -> Optional[dict]:
        """Decides which server is relevant for the user query."""
        server_descriptions = "\n".join([
            f"- {s['name']}: {s['description']}" for s in self.servers
        ])
        
        system_prompt = (
            "You are an MCP Router. Below is a list of available servers and their capabilities:\n"
            f"{server_descriptions}\n\n"
            "Given the user's query, return ONLY the name of the most relevant server. "
            "If none match, return 'None'."
        )
        
        response = await self.llm.ainvoke([
            ("system", system_prompt),
            ("user", query)
        ])
        
        target_name = response.content.strip()
        return next((s for s in self.servers if s["name"] == target_name), None)

class MCPConnection:
    """Manages the lifecycle of the MCP connection."""
    def __init__(self, url: str):
        self.url = url
        self.session: Optional[ClientSession] = None
        self._exit_stack = AsyncExitStack()

    async def __aenter__(self):
        print(f"[*] Attempting to connect to: {self.url}")
        try:
            sse_ctx = sse_client(self.url)
            streams = await self._exit_stack.enter_async_context(sse_ctx)
            read_stream, write_stream = streams
            
            session_ctx = ClientSession(read_stream, write_stream)
            self.session = await self._exit_stack.enter_async_context(session_ctx)
            
            await self.session.initialize()
            return self
        except Exception as e:
            print(f"[!] Connection failed: {e}")
            await self._exit_stack.aclose()
            raise

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print(f"[*] Closing connection to: {self.url}")
        await self._exit_stack.aclose()

    async def get_tools_and_instructions(self):
        if not self.session:
            raise RuntimeError("MCP Session not connected")
        mcp_tools = await self.session.list_tools()
        try:
            mcp_prompt = await self.session.get_prompt("math_assistant_instructions")
            instruction = mcp_prompt.messages[0].content.text
        except:
            instruction = "You are a helpful assistant using the provided tools."
        return mcp_tools.tools, instruction

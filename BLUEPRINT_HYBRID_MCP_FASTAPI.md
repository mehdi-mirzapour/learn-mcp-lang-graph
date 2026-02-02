# 🏗️ Blueprint: Hybrid FastMCP + FastAPI Server

This blueprint outlines the best practices for building a **Hybrid Server** that simultaneously serves as a **Model Context Protocol (MCP)** server for AI agents and a **FastAPI REST API** for traditional clients.

---

## 🎯 The Core Philosophy
**One Logic, Two Interfaces.** 
Always separate your "Business Logic" from the "Transport Layer". This ensures that your calculations, data fetches, or system actions behave identically whether called by an LLM via MCP or by a frontend via REST.

---

## 🛠️ 1. Project Structure & Setup

### Dependency Management
Use `uv` for modern, fast dependency management.
```bash
uv add fastapi uvicorn mcp[cli]
```

### File Layout
Keep it simple. For a single service, `server.py` is enough. For larger projects, move business logic to a `/services` or `/core` directory.

---

## 🧬 2. The Hybrid Implementation Pattern

### A. Shared Business Logic
Define your core functions independently. **Do not** put logic directly inside the tool or route decorators.

```python
def calculate_growth(initial: float, rate: float) -> float:
    if rate < -1:
        raise ValueError("Rate cannot be less than -100%")
    return initial * (1 + rate)
```

### B. Dual Decorators
Use the shared logic in both interfaces.

```python
# --- MCP Interface ---
@mcp.tool()
def growth_tool(initial: float, rate: float) -> float:
    """Calculate financial growth based on initial value and rate."""
    return calculate_growth(initial, rate)

# --- REST Interface ---
@app.get("/growth")
async def growth_endpoint(initial: float, rate: float):
    try:
        result = calculate_growth(initial, rate)
        return {"result": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### C. Mounting the MCP App
This is the "magic" step. Mount the MCP SSE application onto the FastAPI root or a sub-path.

```python
# Option 1: Mount on root (access via /sse and /messages)
app.mount("/", mcp.sse_app())

# Option 2: Mount on sub-path (access via /mcp/sse and /mcp/messages)
app.mount("/mcp", mcp.sse_app())
```

---

## 🛡️ 3. Best Practices checklist

- [ ] **Error Handling**: Use standard Python exceptions in business logic. Map them to `HTTPException` in FastAPI routes, but let FastMCP handle them (it wraps them in JSON-RPC error responses automatically).
- [ ] **CORS Middleware**: Always enable CORS if you plan to access the REST API or SSE from a browser/web-app.
- [ ] **Type Safety**: Use Pydantic models or Python type hints (`float`, `int`, `str`). FastMCP and FastAPI both use these for automatic validation and documentation.
- [ ] **Docstrings**: MCP relies heavily on docstrings to explain tools to the LLM. REST uses them for Swagger documentation. Keep them descriptive!
- [ ] **Sequential Tooling**: If your agent is performing complex steps, use `parallel_tool_calls=False` in your LLM binding to prevent race conditions in the hybrid state.

---

## 🚀 4. Standard Boilerplate

Use this as a starting point for every new hybrid server:

```python
from fastapi import FastAPI, HTTPException
from mcp.server.fastmcp import FastMCP
from starlette.middleware.cors import CORSMiddleware
import uvicorn

# Initialization
app = FastAPI(title="Hybrid API")
mcp = FastMCP("MyMCPService")

# 1. Business Logic
def my_operation(data: str) -> str:
    return f"Processed: {data}"

# 2. MCP Tools
@mcp.tool()
def process_data(text: str) -> str:
    """Expose operation to AI Agents."""
    return my_operation(text)

# 3. REST Endpoints
@app.get("/process")
async def rest_process(text: str):
    """Expose operation to REST clients."""
    return {"message": my_operation(text)}

# 4. Connection & Middleware
app.mount("/", mcp.sse_app())
app.add_middleware(CORSMiddleware, allow_origins=["*"])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## 📖 5. Key Documentation Links
- **REST Docs**: `http://localhost:8000/docs` (Swagger)
- **MCP SSE**: `http://localhost:8000/sse`
- **MCP Inspector**: `npx @modelcontextprotocol/inspector http://localhost:8000/sse`

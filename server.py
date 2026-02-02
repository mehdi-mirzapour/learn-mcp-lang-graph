from fastapi import FastAPI, HTTPException
from mcp.server.fastmcp import FastMCP
from starlette.middleware.cors import CORSMiddleware
import uvicorn

# 1. Create the FastAPI application
app = FastAPI(title="Math Hybrid Server")

# 2. Create the MCP server
# We'll use this to register tools and prompts for the MCP protocol
mcp = FastMCP("MathServer")

# --- SHARED LOGIC ---

def do_add(a: float, b: float) -> float:
    return a + b

def do_subtract(a: float, b: float) -> float:
    return a - b

def do_multiply(a: float, b: float) -> float:
    return a * b

def do_divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

# --- MCP TOOLS ---
# These are exposed to the MCP-capable agents (like agent.py)

@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers."""
    return do_add(a, b)

@mcp.tool()
def subtract(a: float, b: float) -> float:
    """Subtract b from a."""
    return do_subtract(a, b)

@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return do_multiply(a, b)

@mcp.tool()
def divide(a: float, b: float) -> float:
    """Divide a by b. Raises error if b is zero."""
    return do_divide(a, b)

# --- MCP PROMPTS ---

@mcp.prompt()
def math_assistant_instructions() -> str:
    """Instructional prompt for the math assistant."""
    return (
        "You are a helpful mathematical assistant. "
        "IMPORTANT: You must perform calculations STEP-BY-STEP. "
        "Wait for the result of one tool call before starting the next. "
        "Do not attempt to call multiple tools in parallel for a single equation. "
        "Use the result of your previous tool calls to build the final answer."
    )

# --- FASTAPI REST ENDPOINTS ---
# These are exposed as standard REST endpoints for any HTTP client

@app.get("/")
async def root():
    return {
        "status": "active", 
        "service": "Math Hybrid Server",
        "capabilities": ["MCP (SSE)", "REST (JSON)"]
    }

@app.get("/add")
async def rest_add(a: float, b: float):
    return {"operation": "add", "a": a, "b": b, "result": do_add(a, b)}

@app.get("/subtract")
async def rest_subtract(a: float, b: float):
    return {"operation": "subtract", "a": a, "b": b, "result": do_subtract(a, b)}

@app.get("/multiply")
async def rest_multiply(a: float, b: float):
    return {"operation": "multiply", "a": a, "b": b, "result": do_multiply(a, b)}

@app.get("/divide")
async def rest_divide(a: float, b: float):
    try:
        return {"operation": "divide", "a": a, "b": b, "result": do_divide(a, b)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- MOUNT MCP SSE ---
# We mount the MCP SSE app. In servers.json, the URL is http://127.0.0.1:8000/sse
# Mounting internal MCP routes to the root app.
app.mount("/", mcp.sse_app())

if __name__ == "__main__":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    print("🚀 Starting Hybrid Math Server on http://127.0.0.1:8000")
    print("📍 REST API: http://127.0.0.1:8000/docs")
    print("📍 MCP SSE:  http://127.0.0.1:8000/sse")
    
    uvicorn.run(app, host="127.0.0.1", port=8000)

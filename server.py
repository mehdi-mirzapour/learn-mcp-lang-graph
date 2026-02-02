from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
import uvicorn

# Create an MCP server for Math operations
mcp = FastMCP("MathServer")

# --- TOOLS ---

@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b

@mcp.tool()
def subtract(a: float, b: float) -> float:
    """Subtract b from a."""
    return a - b

@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b

@mcp.tool()
def divide(a: float, b: float) -> float:
    """Divide a by b. Raises error if b is zero."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

# --- PROMPTS ---

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

# --- HEALTH CHECK ---
@mcp.custom_route("/", methods=["GET"])
async def home(request):
    return JSONResponse({"status": "active", "service": "MathServer MCP"})

if __name__ == "__main__":
    app = mcp.sse_app()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    print("Starting MathServer MCP server on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)

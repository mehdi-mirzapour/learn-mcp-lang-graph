# 🎓 Learn-MCP-LangGraph: A Math Agent Tutorial 🎓

### 🚀 A Practical Guide to LangChain + OpenAI + Model Context Protocol (MCP)

Welcome! This is a educational tutorial designed to show you how to combine **LangChain orchestration**, **OpenAI intelligence**, and the **Model Context Protocol (MCP)** into a functional, multi-server math agent. 🧠🚀

---

## 💡 What You'll Learn

This project is a starting point to help you understand how to navigate a distributed agent architecture. It demonstrates:
1.  🎯 **Simple Routing**: How to use an LLM to select a relevant server from a list.
2.  🔌 **On-Demand Connections**: Opening SSE (Server-Sent Events) connections only when needed.
3.  🔄 **LangGraph Workflow**: Building a basic cyclic graph to manage "thinking" and "tool use."
4.  🛡️ **Schema Integration**: Turning MCP definitions into Pydantic models for LangChain.

---

## 🗺️ Visualizing the Flow

### 1. The High-Level Architecture
This diagram shows how a user query is routed to the correct server and processed.

```mermaid
sequenceDiagram
    participant U as User
    participant R as Router (LLM)
    participant C as Client (SSE)
    participant S as MCP Server
    
    U->>R: "What is 10 + 20?"
    R->>R: Search servers.json
    R-->>U: Selected: MathServer
    U->>C: Connect to http://127.0.0.1:8000
    C->>S: SSE Handshake & Init
    S-->>C: list_tools (add, subtract...)
    C-->>U: Active Session
```

### 2. The LangGraph State Machine
Once connected, the agent follows this cyclic graph to solve the query.

```mermaid
graph TD
    Start((Start)) --> Agent[Agent Node: Think]
    Agent --> Condition{Need Tool?}
    Condition -- Yes --> Tools[Tools Node: Execute MCP]
    Tools --> Agent
    Condition -- No --> End((End))
```

---

## 🏗️ Project Structure

We've organized the code into three clear parts to make it easy to follow:

| Component | Role | Description |
| :--- | :--- | :--- |
| **`server.py`** | 🧮 **The Math Server** | A simple FastMCP server that provides basic arithmetic tools. |
| **`client.py`** | 🌉 **The Connection Handler** | Manages the SSE handshake and the server registry lookup. |
| **`agent.py`** | 🤖 **The Agent Logic** | The LangGraph definition and the interactive user loop. |

---

## 🚦 Getting Started

### 1️⃣ Setup the Environment 🛠️
We recommend using [uv](https://github.com/astral-sh/uv) for fast dependency management.

```bash
# Install dependencies
uv sync

# Add your OpenAI API key to a .env file
echo "OPENAI_API_KEY=your_sk_key_here" > .env
```

### 2️⃣ Run the Tutorial 🚀

**Step A: Start the MCP Server (Terminal 1)**
```bash
uv run python server.py
```

**Step B: Start the Agent (Terminal 2)**
```bash
uv run python agent.py
```

---

## 🧪 Testing the Server

You can also test the MCP server independently using the **MCP Inspector**:

```bash
pnpm dlx @modelcontextprotocol/inspector http://127.0.0.1:8000/sse
```

---

## 📖 Why This Pattern?

-   **Modular Design**: Keeping the connection logic (`client.py`) separate from the AI logic (`agent.py`) makes your code cleaner. 📁
-   **Registry Driven**: By using a `servers.json`, you can easily experiment with adding more (imaginary or real) servers to see how routing works. 📋
-   **LangGraph Visualization**: Using a graph state machine helps you track exactly what the agent is doing at each step. 📈

---

### 🤝 About This Project

This is a learning resource for the developer community. If you have questions or want to suggest improvements to the tutorial, feel free to open an issue or pull request! 🚀🌌

---
*Developed for teaching Advanced Agentic Coding concepts.*

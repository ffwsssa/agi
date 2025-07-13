# IQuote – Cross-Protocol Quoting System

> End-to-end view for slide decks, docs, and ASI-One onboarding

---

## 1. Discovery from ASI-One / Agentverse

| Item | Value |
|------|-------|
| Public agent profile | <https://agentverse.ai/agents/details/agent1qvsa5pv2uqzs6ezsqt8zs98ldqf86z45kayk0hltx0gtuyuf7svggd6ejde/profile> |
| Alias in ASI-One      | **IQuote** |
| Local implementation  | `solution_architect_agent.py` |

ASI-One can locate the **IQuote** agent via the profile link above and add it to autonomous task graphs. The **Solution Architect Agent** implements the Chat Protocol and serves as the main entry point for ASI-One interactions.

---

## 2. Component Topology

```
ASI-One Orchestrator / Task Graph (HTTP / A2A)
        │  Chat Protocol / JSON-RPC 2.0
        ▼
Solution Architect Agent (8002, uAgent + Chat Protocol) ─►  Gemini 2.5 Flash LLM
        │                                                 │
        ├─► Local Data Agent (8003, A2A) ────────────────► LangChain LLM
        │                                                 │
        ├─► Monday Data Agent (8005, A2A) ───────────────► Monday.com API
        │                                                 │
        └─► MCP Server (sequential-thinking) ────────────► Chain of Thought
```

*Key relationships*

* **Solution Architect Agent** (*IQuote alias*) is the main agent discoverable by ASI-One, implementing Chat Protocol for direct communication.
* **Gemini 2.5 Flash LLM** is embedded within the Solution Architect Agent for ultra-fast reasoning and natural language processing.
* **Local Data Agent** provides enhanced proposal generation via LangChain when needed.
* **Monday Data Agent** supplies real-time SKU and project data from Monday.com.
* **MCP Server** provides sequential thinking capabilities for complex reasoning tasks.

### Chat Protocol Implementation (code excerpt)

```python
# solution_architect_agent.py
from uagents import Agent, Context, Protocol
from uagents.communication import ChatMessage, ChatResponse

# Chat Protocol for ASI-One compatibility
chat_protocol = Protocol("Chat", "1.0.0")

@chat_protocol.on_message(ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    # Process natural language requirement
    requirement = msg.text
    
    # Generate solution using Gemini 2.5 Flash
    solution = await generate_solution(requirement)
    
    # Coordinate with supporting agents if needed
    enhanced_solution = await coordinate_with_agents(solution)
    
    # Return Chat Protocol response
    await ctx.send(sender, ChatResponse(text=enhanced_solution))
```

This illustrates how the agent:
1. Implements Chat Protocol for ASI-One compatibility
2. Processes natural language requirements directly
3. Coordinates with supporting agents as needed
4. Returns structured responses via Chat Protocol

---

## 3. Tech Stack & Patterns

| Layer | Implementation |
|-------|----------------|
| Main Protocol | uAgent + Chat Protocol for ASI-One |
| Supporting Protocols | A2A (JSON-RPC) for agent coordination |
| Runtime | `uagents` (asyncio) |
| LLM Integration | Embedded Gemini 2.5 Flash + LangChain coordination |
| MCP | `sequential-thinking` server for deep CoT reasoning |
| Patterns | Direct Chat Protocol, Agent coordination, Pydantic type safety, full async I/O |

---

## 4. End-to-End Message Flow

1. **ASI-One Orchestrator → Solution Architect Agent** using Chat Protocol (direct communication).
2. **Solution Architect Agent** processes the natural language requirement using embedded Gemini 2.5 Flash.
3. **Solution Architect Agent** coordinates with supporting agents:
   - **Local Data Agent** for enhanced proposal generation (optional)
   - **Monday Data Agent** for real-time SKU/project data (optional)
   - **MCP Server** for complex reasoning tasks (optional)
4. **Solution Architect Agent** returns structured solution via Chat Protocol to ASI-One.

---

## 5. Deployment Cheat Sheet

```bash
# Terminal 1 – Main Agent (IQuote alias) - ASI-One entry point
python IQuote/solution_architect_agent.py   # port 8002

# Terminal 2 – Supporting Local Data Agent (optional)
python IQuote/local_data_agent.py   # port 8003

# Terminal 3 – Supporting Monday Data Agent (optional)
python IQuote/monday_data_agent.py  # port 8005

# Terminal 4 – MCP Server (optional)
python -m sequential_thinking_server  # for complex reasoning

# Quick demo (spawns all interactions)
python IQuote/demo_system.py
```

---

## 6. Framework Integration

### uAgents Framework
- **Chat Protocol**: Direct ASI-One communication
- **Agent Discovery**: Registered on Agentverse
- **Natural Language**: Process requirements in plain English

### LangChain Integration
- **Supporting Agent**: Local Data Agent uses LangChain for enhanced proposals
- **LLM Orchestration**: Coordinate multiple LLM calls when needed

### MCP Integration
- **Sequential Thinking**: Complex reasoning and chain-of-thought
- **Extensibility**: Custom MCP servers for domain-specific logic

---

## 7. Future Enhancements

* **CrewAI Integration**: Multi-agent orchestration for complex tasks
* **LangGraph**: Workflow orchestration for complex solution processes
* **Vector Store MCP**: Long-term memory for customer preferences
* **Real-time Analytics**: Performance monitoring and optimization
* **Automated Scaling**: Container orchestration for high availability

---

**Ready for slides:** copy any section straight into PowerPoint or Notion.

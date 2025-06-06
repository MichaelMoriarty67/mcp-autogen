from fastapi import FastAPI, HTTPException
from typing import Dict
from uuid import uuid4

from agent_manager import AgentManager
from tool_registry import ToolRegistry
from schemas import StartAgentRequest, ChatRequest, ChatResponse, AppMetadata
from utils import openai_tool_call_parser
from scrape import read_apps

from mcp_agent.app import MCPApp as mcp_app_raw
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM

app = FastAPI()

# === Global MCP App and Agent Sessions ===
mcp_agent_app = None
agent_sessions: Dict[str, AgentManager] = {}

# === LLM options available ===
LLM_MAP = {
    "openai": OpenAIAugmentedLLM,
    # Add more LLMs here
}

tool_registry_path = "./mcp_agent.config.yaml"
TOOL_REGISTRY = ToolRegistry(tool_registry_path)


# === Startup MCP runtime ===
@app.on_event("startup")
async def startup_event():
    global mcp_agent_app
    mcp_agent_app = mcp_app_raw(name="hmfai")
    print("[MCP] Agent app initialized.")


# === Shutdown MCP runtime and agents ===
@app.on_event("shutdown")
async def shutdown_event():
    global mcp_agent_app

    print("[MCP] Shutting down agent sessions...")
    for manager in agent_sessions.values():
        await manager.shutdown()

    if mcp_agent_app:
        await mcp_agent_app.cleanup()
        print("[MCP] Agent app shut down.")


# === Start an agent session ===
@app.post("/start-agent")
async def start_agent(req: StartAgentRequest):
    if req.llm not in LLM_MAP:
        raise HTTPException(status_code=400, detail="Invalid LLM")

    # Validate tools
    all_tool_names = [t.name for t in TOOL_REGISTRY.list_tools()]
    unknown_tools = [
        t.tool_name for t in req.tools if t.tool_name not in all_tool_names
    ]
    if unknown_tools:
        raise HTTPException(status_code=400, detail=f"Unknown tools: {unknown_tools}")

    tools_with_credentials = [t.model_dump() for t in req.tools]

    agent_id = str(uuid4())
    manager = AgentManager(
        agent_id=agent_id,
        llm_class=LLM_MAP[req.llm],
        tools_with_credentials=tools_with_credentials,
        instruction=req.instruction,
        tool_call_parser=openai_tool_call_parser,
    )

    await manager.start(mcp_agent_app)
    agent_sessions[agent_id] = manager

    return {"agent_id": agent_id}


# === Chat with an agent session ===
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    manager = agent_sessions.get(req.agent_id)
    if not manager:
        raise HTTPException(status_code=404, detail="Agent not found")

    result = await manager.chat(req.message)
    return result


@app.get("/tools/available")
def get_available_tools():
    return [tool.model_dump() for tool in TOOL_REGISTRY.list_tools()]


@app.get("/apps/available", response_model=list[AppMetadata])
def get_available_apps():
    return read_apps()

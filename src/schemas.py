from pydantic import BaseModel
from typing import Dict, List


class ToolCredential(BaseModel):
    tool_name: str
    credentials: Dict[str, str]


class StartAgentRequest(BaseModel):
    llm: str  # e.g. "openai"
    instruction: str
    tools: List[ToolCredential]


class ChatRequest(BaseModel):
    agent_id: str
    message: str


class ToolCall(BaseModel):
    tool_name: str
    function: str
    args: Dict[str, str]
    result: Dict  # Or List, depending on how your tools return data


class ChatResponse(BaseModel):
    reply: str
    tool_calls: List[ToolCall]

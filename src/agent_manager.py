from typing import List, Optional, Dict, Callable
from mcp_agent.agents.agent import Agent, LLM
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM
from uuid import uuid4
from schemas import ToolCall, ChatResponse
from local_tools import add_new_tool


class AgentManager:
    def __init__(
        self,
        agent_id: str,
        llm_class: OpenAIAugmentedLLM,
        tools_with_credentials: List[Dict],
        instruction: str,
        tool_call_parser: Callable[[List[Dict]], List["ToolCall"]],
    ):
        self.agent_id = agent_id
        self.llm_class = llm_class
        self.tools_with_credentials = tools_with_credentials
        self.instruction = instruction
        self.agent: Optional[Agent] = None
        self.llm: LLM | None = None
        self.started = False
        self.logger = None
        self.tool_call_parser = tool_call_parser

    async def start(self, mcp_agent_app):
        if self.started:
            return

        self.logger = mcp_agent_app.logger

        self.agent = Agent(
            name="assistant",
            instruction=self.instruction,
            server_names=[tool["tool_name"] for tool in self.tools_with_credentials],
            functions=[add_new_tool],
        )

        await self.agent.__aenter__()

        # Attach the LLM to the agent
        self.llm = await self.agent.attach_llm(self.llm_class)
        self.started = True

    async def chat(self, message: str) -> ChatResponse:
        if not self.started:
            raise RuntimeError("Agent not started")

        reply = await self.llm.generate_str(message=message)
        history = self.llm.history.get()
        parsed_tool_calls = self.tool_call_parser(history)

        return {
            "reply": reply,
            "tool_calls": [call.model_dump() for call in parsed_tool_calls],
        }

    async def shutdown(self):
        if self.started and self.agent:
            await self.agent.__aexit__(None, None, None)
            self.started = False

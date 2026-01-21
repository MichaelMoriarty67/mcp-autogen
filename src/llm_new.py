from schemas import Tool, LLMAgnosticMessage
from typing import List, Optional, TypeVar, Generic
from abc import ABC, abstractmethod
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

# this will manage the llm and its history


# agent, it can send requests to any llm
# as long as the history can be converted


# wraps server and manages tools for LLM
class App:
    def __init__(self, name, server):
        self.name = name
        self.server = server
        self.tools: List[Tool] = self._load_tools()
        self.active_tools: List[Tool] = []

    def _load_tools(self) -> List[Tool]:
        """Load all available tools from the server."""
        raw_tools = self.server.list_tools()
        return [
            Tool(
                name=tool["name"],
                description=tool.get("description", ""),
                parameters=tool.get("inputSchema", {}),
            )
            for tool in raw_tools
        ]

    def activate_tool(self, tool_name: str) -> bool:
        """
        Activate a tool to make it available to the LLM.

        Args:
            tool_name: Name of the tool to activate

        Returns:
            True if tool was activated, False if not found or already active
        """
        # Check if already active
        if any(t.name == tool_name for t in self.active_tools):
            print(f"Tool '{tool_name}' is already active")
            return False

        # Find tool in available tools
        tool = next((t for t in self.tools if t.name == tool_name), None)
        if tool:
            self.active_tools.append(tool)
            print(f"Activated tool '{tool_name}' in app '{self.name}'")
            return True
        else:
            print(f"Tool '{tool_name}' not found in app '{self.name}'")
            return False

    def deactivate_tool(self, tool_name: str) -> bool:
        """
        Deactivate a tool to remove it from LLM availability.

        Args:
            tool_name: Name of the tool to deactivate

        Returns:
            True if tool was deactivated, False if not found in active tools
        """
        for i, tool in enumerate(self.active_tools):
            if tool.name == tool_name:
                self.active_tools.pop(i)
                print(f"Deactivated tool '{tool_name}' in app '{self.name}'")
                return True

        print(f"Tool '{tool_name}' is not active in app '{self.name}'")
        return False

    def activate_all_tools(self):
        """Activate all available tools."""
        self.active_tools = self.tools.copy()
        print(f"Activated all {len(self.tools)} tools in app '{self.name}'")

    def deactivate_all_tools(self):
        """Deactivate all tools."""
        self.active_tools = []
        print(f"Deactivated all tools in app '{self.name}'")


LLMMessageType = TypeVar("LLMMessageType")


class BaseLLM(ABC, Generic[LLMMessageType]):
    def __init__(self, model_name: str, api_key: Optional[str] = None):
        self.api_key = api_key
        self.model_name = model_name

    @abstractmethod
    def generate(self, messages: List[LLMAgnosticMessage]) -> LLMAgnosticMessage:
        pass

    @abstractmethod
    def convert_messages(
        self, messages: List[LLMAgnosticMessage]
    ) -> List[LLMMessageType]:
        pass

    @abstractmethod
    def convert_back(self) -> List[LLMAgnosticMessage]:
        pass


class OpenAILLM(BaseLLM[ChatCompletionMessageParam]):
    def __init__(self, model_name: str = "gpt-5-nano", api_key: str | None = None):
        super().__init__(model_name, api_key)
        self.client = OpenAI(api_key=api_key)

    def generate(self, messages: List[LLMAgnosticMessage]) -> LLMAgnosticMessage:
        openai_messages = self.convert_messages(messages)
        response = self.client.responses.create(input=openai_messages)

    def convert_messages(
        self, messages: List[LLMAgnosticMessage]
    ) -> List[ChatCompletionMessageParam]:
        new_msgs = []
        for message in messages:
            new_msg = {}

            if message.role == "system":
                new_msg["role"] = "developer"
            else:
                new_msg["role"] = message.role

            if message.content:
                new_msg["content"] = message.content

            if message.tool_calls and len(message.tool_calls) > 0:
                new_msg["tool_calls"] = []
                for tool_call in message.tool_calls:
                    new_tool_call = {"id": tool_call.id, "type": "function"}
                    new_tool_args = {
                        "name": tool_call.name,
                        "arguments": tool_call.arguments,
                    }
                    new_tool_call["function"] = new_tool_args
                    new_msg["tool_calls"].append(new_tool_call)

            new_msgs.append(new_msg)

        return new_msgs


class Agent:
    def __init__(self, system_msg):
        self.history: List[LLMAgnosticMessage] = []
        self.apps = []
        self.system_message = system_msg

    def generate(self, prompt: str):
        pass

    def add_app(self, app: App):
        self.apps.append(app)

    def remove_app(self, name: str):
        for i, app in enumerate(self.apps):
            if app.name == name:
                self.apps.pop(i)
                print(f"Removed app '{name}'")
                return True

        print(f"App '{name}' not found")
        return False

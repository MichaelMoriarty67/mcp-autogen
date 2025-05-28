from typing import Callable, List, TypeVar, Type, Generic
from abc import ABC, abstractmethod
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionContentPartParam,
    ChatCompletionContentPartTextParam,
    ChatCompletionContentPartRefusalParam,
    ChatCompletionMessage,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)

InputMessageT = TypeVar("InputMessageT")
OutputMessageT = TypeVar("OutputMessageT")

MessageParamsT = TypeVar("MessageParamsT")
MessageResultT = TypeVar("MessageResultT")
ModelT = TypeVar("ModelT")

class LLMMessageConverter(ABC, Generic[InputMessageT, OutputMessageT]):
    @abstractmethod
    def convert(self, message: InputMessageT) -> OutputMessageT:
        """Convert an LLM message of one type to another."""
        pass
    
    @abstractmethod
    def convert_back(self, output: OutputMessageT) -> InputMessageT:
        """Converts an LLM output message back to the Agent input message type."""
        pass

class LLM:
    def __init__(self, messages_converter: MessagesConverter)
    def call_llm(self, params: MessageParamsT) -> MessageResultT: ...


class OpenAIMessageConverter(LLMMessageConverter[AgentMessage, ChatCompletionMessageParam]):
    def convert(self, message: AgentMessage) -> ChatCompletionMessageParam:
        pass

    def convert_back(self, output):
        return super().convert_back(output)
    


class Agent:
    def __init__(
        self,
        name: str,
        instructions: str | None,
        llm: LLM,
        tools: ToolsConnection,
        functions: List[Callable] = None,
    ):
        self.name = (name,)
        self.instructions = instructions or ""
        self.tools = tools
        self.functions = functions or []

        self.history = []

    
    def generate(self, message: str)

    def str_response(self, message: str) -> str:
        ...
    
    def structured_response(self, message: str, response_model: Type[ModelT]) -> ModelT:
        ...
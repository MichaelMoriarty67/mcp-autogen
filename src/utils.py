import ast
from schemas import ToolCall
from typing import List


def openai_tool_call_parser(history: List[dict]) -> List[ToolCall]:
    tool_calls_with_results = []
    i = 0

    while i < len(history):
        message = history[i]

        if "tool_calls" in message:
            for tool_call in message["tool_calls"]:
                tool_name = tool_call.function.name.split("_")[0]
                function = tool_call.function.name
                args = ast.literal_eval(tool_call.function.arguments or "{}")

                result = {}
                if i + 1 < len(history):
                    result_msg = history[i + 1]
                    if (
                        result_msg["role"] == "tool"
                        and result_msg.get("tool_call_id") == tool_call.id
                    ):
                        try:
                            result = ast.literal_eval(result_msg["content"])
                        except Exception:
                            result = {"raw": result_msg["content"]}

                tool_calls_with_results.append(
                    ToolCall(
                        tool_name=tool_name, function=function, args=args, result=result
                    )
                )
        i += 1

    return tool_calls_with_results

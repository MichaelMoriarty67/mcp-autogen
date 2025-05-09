from typing import List
import yaml
from pathlib import Path
from schemas import ToolType, ToolMetadata


class ToolRegistry:
    def __init__(self, config_path: str):
        if not config_path:
            raise ValueError("A valid config_path must be provided.")
        self.config_path = config_path
        self.apps: List[ToolMetadata] = []
        self.load()

    def load(self):
        config = yaml.safe_load(Path(self.config_path).read_text())
        server_configs = config.get("mcp", {}).get("servers", {})

        for name, server in server_configs.items():
            command = server.get("command", "")
            tool_type = (
                ToolType.NODE
                if "npx" in command
                else ToolType.PYTHON if "uvx" in command else ToolType.OTHER
            )

            tool = ToolMetadata(
                name=name,
                command=command,
                args=server.get("args", []),
                type=tool_type,
                description=server.get("description", None),
            )
            self.apps.append(tool)

    def list_tools(self) -> List[ToolMetadata]:
        return self.apps

    def get_tool(self, name: str) -> ToolMetadata:
        return next(tool for tool in self.apps if tool.name == name)

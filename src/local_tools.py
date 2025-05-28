import yaml

MCP_CONFIG_PATH = "mcp_agent.config.yaml"  # Global path to your YAML file


def add_new_tool(name: str, command: str, args: list[str], description: str):
    """
    Adds or updates a tool entry in the 'servers' section of the MCP YAML config.

    Args:
        name (str): Name of the tool (e.g. "filesystem").
        command (str): Command to run the tool (e.g. "npx").
        args (list[str]): List of arguments to pass to the command.
        description (str): A human-readable description of the tool.
    """
    # Load existing config
    with open(MCP_CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)

    # Ensure 'servers' exists
    if "mcp" not in config:
        config["mcp"] = {}
    if "servers" not in config["mcp"]:
        config["mcp"]["servers"] = {}

    # Update the tool
    config["mcp"]["servers"][name] = {
        "command": command,
        "args": args,
        "description": description,
    }

    # Write the updated config back to the file
    with open(MCP_CONFIG_PATH, "w") as f:
        yaml.safe_dump(config, f, sort_keys=False)

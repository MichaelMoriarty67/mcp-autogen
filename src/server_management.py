import yaml
import subprocess
import time
import requests

BASE_PORT = 8080
CLIENT_NAME = "HMFAI_APP"

running_servers = {}
servers_yaml_path = "./mcp_agent.config.yaml"


class MCPServer:
    """Interface for interacting with a running MCP server."""

    def __init__(self, name, process, port):
        self.name = name
        self.process = process
        self.port = port
        self._initialized = False
        self._session_id = None

    @property
    def url(self):
        """Get the HTTP URL for this server."""
        return f"http://localhost:{self.port}/mcp"

    @property
    def pid(self):
        """Get the process ID."""
        return self.process.pid

    @property
    def is_running(self):
        """Check if the server process is still running."""
        return self.process.poll() is None

    def __repr__(self):
        status = "running" if self.is_running else "stopped"
        return f"MCPServer(name='{self.name}', url='{self.url}', pid={self.pid}, status={status})"

    def list_tools(self):
        """
        Get a list of available tools from this MCP server.

        Returns:
            List of tool objects with name, description, and input schema
        """
        if not self._initialized:
            if not self._initialize_connection():
                return []

        try:
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
            if self._session_id:
                headers["mcp-session-id"] = self._session_id

            # Send JSON-RPC request to list tools
            response = requests.post(
                self.url,
                json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()

            result = response.json()

            # Extract tools from the response
            if "result" in result and "tools" in result["result"]:
                return result["result"]["tools"]
            else:
                print(f"Unexpected response format: {result}")
                return []

        except requests.exceptions.RequestException as e:
            print(f"Error listing tools for {self.name}: {e}")
            return []

    def _initialize_connection(self) -> bool:
        """Initialize the MCP connection (must be called before using the server)."""
        try:
            # Send initialize request
            response = requests.post(
                self.url,
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": CLIENT_NAME, "version": "0.1.0"},
                    },
                    "id": 0,
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                timeout=10,
            )
            response.raise_for_status()

            # Extract session ID from response headers
            self._session_id = response.headers.get("mcp-session-id")

            # Send initialized notification
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
            if self._session_id:
                headers["mcp-session-id"] = self._session_id

            requests.post(
                self.url,
                json={"jsonrpc": "2.0", "method": "initialized", "params": {}},
                headers=headers,
                timeout=10,
            )
            return True

        except requests.exceptions.RequestException as e:
            print(f"Error initializing connection to {self.name}: {e}")
            return False


def get_servers():
    return running_servers


def start_servers():
    with open(servers_yaml_path, "r") as file:
        data = yaml.safe_load(file)

    servers = data["mcp"]["servers"]
    port = BASE_PORT

    for server_name, config in servers.items():
        command = config["command"]
        args = config.get("args", [])

        # Build the proxy command - pass server command and args separately
        proxy_command = [
            "mcp-proxy",
            f"--port={port}",
            "--",  # This tells mcp-proxy "everything after this is the server command"
            command,
        ] + args

        # Start the proxy process
        process = subprocess.Popen(
            proxy_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        # Create MCPServer object
        server = MCPServer(server_name, process, port)
        running_servers[server_name] = server

        print(f"Started server '{server_name}' on {server.url} (PID {server.pid})")

        port += 1

    # Give servers a moment to start up
    time.sleep(2)

    return running_servers


def kill_servers():
    killed_count = 0

    for server_name, server in running_servers.items():
        if server.is_running:
            server.process.terminate()  # Send SIGTERM
            try:
                server.process.wait(
                    timeout=5
                )  # Wait up to 5 seconds for graceful shutdown
            except subprocess.TimeoutExpired:
                server.process.kill()  # Force kill if it doesn't terminate
                server.process.wait()

            print(
                f"Killed server '{server_name}' on port {server.port} (PID {server.pid})"
            )
            killed_count += 1
        else:
            print(f"Server '{server_name}' was already stopped")

    running_servers.clear()
    return killed_count


if __name__ == "__main__":
    print("\nStarting servers with HTTP proxy...")
    start_servers()

    # Show server info
    print("\nRunning servers:")
    for name, server in get_servers().items():
        print(f"  {server}")
        # Easy access to attributes:
        print(f"    URL: {server.url}")
        print(f"    PID: {server.pid}")
        print(f"    Running: {server.is_running}")
        print(f"    First tool avail: {server.list_tools()[0]}")

    # Do some work...
    print("\nServers running. Press Ctrl+C to stop...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nShutting down...")

    # Kill all servers
    print("Killing servers...")
    kill_servers()

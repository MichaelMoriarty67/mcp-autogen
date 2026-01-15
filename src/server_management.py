import yaml
import subprocess

running_servers = {}
servers_yaml_path = "./mcp_agent.config.yaml"


def get_servers():
    with open(servers_yaml_path, "r") as file:
        yaml_data = yaml.safe_load(file)

    server_names = list(yaml_data["mcp"]["servers"].keys())

    return server_names


def start_servers():
    with open(servers_yaml_path, "r") as file:
        data = yaml.safe_load(file)

    servers = data["mcp"]["servers"]

    for server_name, config in servers.items():
        command = config["command"]
        args = config.get("args", [])

        # Build the full command
        full_command = [command] + args

        # Start the server process
        process = subprocess.Popen(
            full_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        running_servers[server_name] = process
        print(f"Started server '{server_name}' with PID {process.pid}")

    return running_servers


def kill_servers():
    killed_count = 0

    for server_name, process in running_servers.items():
        if process.poll() is None:  # Check if process is still running
            process.terminate()  # Send SIGTERM
            try:
                process.wait(timeout=5)  # Wait up to 5 seconds for graceful shutdown
            except subprocess.TimeoutExpired:
                process.kill()  # Force kill if it doesn't terminate
                process.wait()

            print(f"Killed server '{server_name}' (PID {process.pid})")
            killed_count += 1
        else:
            print(f"Server '{server_name}' was already stopped")

    running_servers.clear()
    return killed_count


if __name__ == "__main__":
    servers = get_servers()
    print("Server names:", list(servers))

    # Start all servers
    print("\nStarting servers...")
    start_servers()

    # Do some work...
    import time

    time.sleep(30)

    # Kill all servers
    print("\nKilling servers...")
    kill_servers()

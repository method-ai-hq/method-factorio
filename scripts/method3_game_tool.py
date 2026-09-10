"""JSON transport for Method 3 tools and run steps. No model calls or game admin."""
import json
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request


def request(endpoint, action):
    if endpoint.startswith("unix:"):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.settimeout(30)
            connection.connect(endpoint.removeprefix("unix:"))
            connection.sendall((json.dumps(action) + "\n").encode())
            return json.loads(connection.makefile("rb").readline(2_000_000))
    parsed = urllib.parse.urlparse(endpoint)
    if parsed.scheme != "http" or parsed.hostname not in ("127.0.0.1", "localhost"):
        raise ValueError("The game endpoint must be a local HTTP or Unix connection")
    message = urllib.request.Request(endpoint, data=json.dumps(action).encode(),
                                     headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(message, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        return json.loads(error.read())


def main():
    data = json.load(sys.stdin)
    operation = sys.argv[1] if len(sys.argv) > 1 else "act"
    if operation == "observe":
        action = {"action": "observe"}
    elif operation == "batch":
        actions = json.loads(data["actions"]) if isinstance(data["actions"], str) else data["actions"]
        action = {"action": "batch", "actions": actions}
    else:
        action = json.loads(data["action"]) if isinstance(data["action"], str) else data["action"]
    result = request(data["endpoint"], action)
    print(json.dumps({"response": json.dumps(result, separators=(",", ":"))}))


if __name__ == "__main__":
    main()

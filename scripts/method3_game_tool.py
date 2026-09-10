"""JSON transport for Method 3 tools and run steps. No model calls or game admin."""
import json
import os
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request


ENDPOINT_ENV = "METHOD3_GAME_ENDPOINT"


def validate_endpoint(endpoint):
    if not isinstance(endpoint, str) or not endpoint or any(c.isspace() for c in endpoint):
        raise ValueError("The game endpoint must be nonempty text without whitespace")
    if endpoint.startswith("unix:"):
        path = endpoint.removeprefix("unix:")
        if not os.path.isabs(path) or "\x00" in path:
            raise ValueError("The game socket path must be absolute")
        return endpoint
    parsed = urllib.parse.urlparse(endpoint)
    if (parsed.scheme != "http" or parsed.hostname not in ("127.0.0.1", "localhost")
            or parsed.username is not None or parsed.password is not None
            or parsed.path != "/action" or parsed.params or parsed.query or parsed.fragment
            or parsed.port is None):
        raise ValueError("The game endpoint must be a local HTTP /action URL with an explicit port")
    return endpoint


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("The game endpoint must not redirect")


def request(endpoint, action):
    bound = os.environ.get(ENDPOINT_ENV)
    if not bound:
        raise ValueError("The operator game endpoint is not bound")
    validate_endpoint(bound)
    if endpoint != bound:
        raise ValueError("The supplied endpoint does not match the operator game endpoint")
    if endpoint.startswith("unix:"):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.settimeout(30)
            connection.connect(endpoint.removeprefix("unix:"))
            connection.sendall((json.dumps(action) + "\n").encode())
            return json.loads(connection.makefile("rb").readline(2_000_000))
    message = urllib.request.Request(endpoint, data=json.dumps(action).encode(),
                                     headers={"Content-Type": "application/json"})
    # Do not let process proxy settings or an HTTP redirect change the destination.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(message, timeout=30) as response:
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

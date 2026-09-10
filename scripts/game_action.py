"""Send one JSON action to the local test host. No game admin connection."""
import argparse
import json
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument("action", help="One JSON action object")
parser.add_argument("--endpoint", default="http://127.0.0.1:18765/action")
args = parser.parse_args()
payload = json.dumps(json.loads(args.action)).encode()
request = urllib.request.Request(args.endpoint, data=payload,
                                 headers={"Content-Type": "application/json"})
with urllib.request.urlopen(request, timeout=100) as response:
    result = json.load(response)
print(json.dumps(result, indent=2))
raise SystemExit(0 if result["ok"] else 1)

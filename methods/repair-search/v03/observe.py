"""One public observe action; no retries and no private state access."""
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request

from compact import EQUIPMENT, compact


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise RuntimeError("Redirect refused")


json.load(sys.stdin)
request = urllib.request.Request(
    os.environ["REPAIR_ENDPOINT"],
    json.dumps({"action": "observe", "names": EQUIPMENT}).encode(),
    {"Content-Type": "application/json"},
)
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
try:
    with opener.open(request, timeout=30) as response:
        observed = json.load(response)
except urllib.error.HTTPError as error:
    observed = json.loads(error.read())
Path("initial-observation.json").write_text(json.dumps(observed))
if not observed.get("ok"):
    raise RuntimeError("Public observation failed: " + json.dumps(observed))
print(json.dumps({"factory": json.dumps(compact(observed["result"]), separators=(",", ":"))}))

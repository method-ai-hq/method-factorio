"""Collect allowed game observations for a native Method model call."""
import json
import sys
import urllib.request

endpoint=json.load(sys.stdin)['endpoint']
observations=[]
for action in [{'action':'observe'},{'action':'nearest','resource':'iron-ore'}]:
    request=urllib.request.Request(endpoint,json.dumps(action).encode(),{'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=25) as response:
        observations.append(json.load(response))
print(json.dumps({'world':json.dumps(observations)}))

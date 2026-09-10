import json
import os
from pathlib import Path
import sys

from repair_method import codex_step

data = json.load(sys.stdin)
instructions = Path("prompt.txt").read_text()
instructions += (
    "\nUse this available Python executable for game calls: /opt/homebrew/bin/python3. "
    "Do not try the command `python`. "
    f"\nCall finish before Unix time {float(os.environ['REPAIR_DEADLINE']) - 10:.1f}. "
    "Use Python time.time() to check real time. The operator reserved additional evaluation time."
)
instructions += "\n\nINITIAL_FACTORY_JSON\n" + data.pop("factory")
print(json.dumps(codex_step(data, instructions)))

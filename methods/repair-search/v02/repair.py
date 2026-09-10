import json
import os
from pathlib import Path
import sys

from repair_method import codex_step

data = json.load(sys.stdin)
instructions = Path("prompt.txt").read_text()
instructions += (
    f"\nCall finish before Unix time {float(os.environ['REPAIR_DEADLINE']) - 10:.1f}. "
    "Use Python time.time() to check real time. The operator reserved additional evaluation time."
)
print(json.dumps(codex_step(data, instructions)))

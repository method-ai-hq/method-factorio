"""Initial Method step. The operator adds the common subscription runner."""
import json
from pathlib import Path
import sys
from repair_method import codex_step

print(json.dumps(codex_step(json.load(sys.stdin), Path("prompt.txt").read_text())))

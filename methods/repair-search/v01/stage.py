"""Bound each stage under the operator's one absolute deadline."""
import json
import os
from pathlib import Path
import sys
import time

from repair_method import codex_step


def run(stage, output_key, seconds=None):
    data = json.load(sys.stdin)
    now = time.time()
    deadline = float(os.environ["REPAIR_DEADLINE"])
    instructions = Path(stage + ".txt").read_text()
    instructions += (
        f"\nThis stage starts at Unix time {now:.1f}. "
        f"Call finish no later than Unix time {deadline - 10:.1f}. "
        "The operator already reserved evaluation time beyond that deadline. "
        "Use Python time.time() to check real time. Stage time does not reset the task clock."
    )
    if seconds is not None:
        instructions += f"\nReturn your stage report before Unix time {min(now + seconds - 12, deadline - 15):.1f}."
    try:
        response = codex_step(data, instructions, max_seconds=seconds)
    except (RuntimeError, TimeoutError) as error:
        response = {
            "report": "The prior stage ended without a complete report. Inspect the current game state before acting. " + str(error),
            "execution_status": "stage_incomplete",
            "evidence": "",
            "remaining_seconds": max(0, deadline - time.time()),
        }
    if output_key == "report":
        print(json.dumps(response))
    else:
        print(json.dumps({output_key: response["report"]}))

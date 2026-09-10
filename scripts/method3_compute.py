"""Restricted in-memory Python calculations and permitted game action batches.

No models, imports, attribute access, files, environment, or arbitrary network.
"""
import ast
import json
import signal
import sys
import time

from method3_game_tool import request


def main():
    def timeout(signum, frame):
        raise TimeoutError("The compute call reached 20 seconds")
    signal.signal(signal.SIGALRM, timeout)
    signal.setitimer(signal.ITIMER_REAL, 20)
    data = json.load(sys.stdin)
    code = data["code"]
    if not isinstance(code, str) or len(code) > 20000:
        raise ValueError("Code must be text of at most 20000 characters")
    tree = ast.parse(code, mode="exec")
    allowed = (ast.Module, ast.Expr, ast.Assign, ast.AugAssign, ast.If, ast.For, ast.While,
               ast.Break, ast.Continue, ast.Pass, ast.Name, ast.Load, ast.Store, ast.Constant,
               ast.List, ast.Tuple, ast.Dict, ast.Set, ast.Subscript, ast.Slice, ast.BinOp,
               ast.UnaryOp, ast.BoolOp, ast.Compare, ast.IfExp, ast.Call, ast.keyword,
               ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp, ast.comprehension,
               ast.operator, ast.unaryop, ast.boolop, ast.cmpop)
    for node in ast.walk(tree):
        if not isinstance(node, allowed):
            raise ValueError(f"Python syntax is not allowed: {type(node).__name__}")
        if isinstance(node, ast.Name) and node.id.startswith("_"):
            raise ValueError("Private Python names are not allowed")
        if isinstance(node, ast.Call) and not isinstance(node.func, ast.Name):
            raise ValueError("Call only a named allowed function")
    started = time.monotonic()
    actions = 0
    printed = []
    lines = 0
    def act(action):
        nonlocal actions
        if actions >= 50:
            raise RuntimeError("The compute call reached 50 game actions")
        if not isinstance(action, dict):
            raise ValueError("act requires an action dictionary")
        actions += 1
        return request(data["endpoint"], action)
    def observe():
        return act({"action": "observe"})
    def limited_print(*values):
        text = " ".join(str(v) for v in values)
        if sum(map(len, printed)) + len(text) > 60000:
            raise RuntimeError("Printed output is too large")
        printed.append(text)
    def trace(frame, event, arg):
        nonlocal lines
        if frame.f_code.co_filename == "<policy-compute>" and event == "line":
            lines += 1
            if lines > 50000 or time.monotonic()-started > 20:
                raise TimeoutError("The compute call reached its work limit")
        return trace
    namespace = {"__builtins__": {}, "act": act, "observe": observe, "print": limited_print,
                 "range": range, "len": len, "int": int, "float": float, "str": str, "bool": bool,
                 "min": min, "max": max, "round": round, "abs": abs, "sum": sum, "sorted": sorted,
                 "list": list, "dict": dict, "enumerate": enumerate, "zip": zip}
    sys.settrace(trace)
    try:
        exec(compile(tree, "<policy-compute>", "exec"), namespace, namespace)
    finally:
        sys.settrace(None)
        signal.setitimer(signal.ITIMER_REAL, 0)
    response = json.dumps({"result": namespace.get("result"), "printed": printed,
                           "game_actions": actions, "line_events": lines})
    if len(response) > 100000:
        raise RuntimeError("The compute result is too large")
    print(json.dumps({"response": response}))


if __name__ == "__main__":
    main()

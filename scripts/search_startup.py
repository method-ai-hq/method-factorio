"""Bounded startup coordination. No game or model calls."""
import fcntl
import json
import os
from pathlib import Path
import time


class StartupFailure(RuntimeError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def write_status(path, **data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f'.{os.getpid()}.tmp')
    temporary.write_text(json.dumps({**data, 'updated_at': time.time()}, indent=2) + '\n')
    temporary.replace(path)


def client_stage(log):
    if 'to(InGame)' in log:
        return 'connected'
    if 'Sprites loaded' in log:
        return 'joining_server'
    return 'loading_graphics'


class StartupGate:
    """Only one native client may load and initialize at a time on this host."""
    def __init__(self, path):
        self.path = Path(path)
        self.stream = None

    def acquire(self, deadline, cancelled=lambda: False):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.stream = self.path.open('a+')
        try:
            while time.time() < deadline and not cancelled():
                try:
                    fcntl.flock(self.stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    return
                except BlockingIOError:
                    time.sleep(min(.1, max(0, deadline-time.time())))
            raise StartupFailure('startup_queue_timeout', 'No startup slot remained before the deadline')
        except BaseException:
            self.close()
            raise

    def close(self):
        if self.stream is not None:
            self.stream.close()  # The kernel also releases this lock on process exit.
            self.stream = None


def recovery_decision(record, attempts, authorized):
    """Only a declared loading timeout can receive one automatic replacement."""
    failure = record.get('infrastructure_failure', {})
    if not failure:
        return 'continue'
    if (authorized and attempts == 1 and failure.get('phase') == 'startup'
            and failure.get('code') == 'graphics_loading_timeout'):
        return 'retry_serial'
    return 'repair_required'

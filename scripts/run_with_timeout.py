#!/usr/bin/env python3

import os
import signal
import subprocess
import sys


timeout_seconds = int(sys.argv[1])
command = sys.argv[2:]
process = subprocess.Popen(command, start_new_session=True)

try:
    result = process.wait(timeout=timeout_seconds)
except subprocess.TimeoutExpired:
    print(
        f"Command timed out after {timeout_seconds}s: {' '.join(command)}",
        file=sys.stderr,
    )
    os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()
    result = 124

raise SystemExit(result)

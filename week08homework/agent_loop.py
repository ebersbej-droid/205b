#!/usr/bin/env python3
"""
Jarrett Ebersberger
COGS205B
Week 8: Agentic loop for implementing BayesFactor using GeminiSimpleAPI.

Usage:
    cd week08homework/
    python agent_loop.py
"""

import subprocess
import sys
from pathlib import Path
import time

# Allow running from week08homework/ without installing the package
_FILES_DIR = Path(__file__).resolve().parent.parent
if str(_FILES_DIR) not in sys.path:
    sys.path.insert(0, str(_FILES_DIR))

from gemini_simple_api import GeminiSimpleAPI # noqa: E402


# --- Paths ---
task_dir = Path(__file__).parent
test_dir = task_dir / "tests"
test_file = test_dir / "test_bayes_factor.py"
source_file = task_dir / "bayes_factor.py"
prompt_file = task_dir / "task.txt"
OUTPUT_FILE = task_dir / "agent_loop_output.txt"

# OS guardrail for the test file
test_file.chmod(0o444)

# --- Parameters ---
MODEL = "gemma-4-31b-it"
MAX_ATTEMPTS = 8
# include unit test in api call
# details leak through failure output anyway
INCLUDE_TEST_FILE = True
# Adding this if we want to add previous attempts from the model
INCLUDE_PREVIOUS_ATTEMPT = False

# --- Client ---
client = GeminiSimpleAPI(
    api_key_file=Path("/workspace/secrets/gemini.json"),
    model=MODEL,
    working_dir=task_dir,
    protected_directories=[test_dir], # extra test file protection
)

# --- Test runner ---
def run_tests() -> tuple[int, str]:
    result = subprocess.run(
        ["python3", "-B", "-m", "unittest", "discover", "-s", test_dir],
        cwd=task_dir,
        capture_output=True,
        text=True,
    )
    return result.returncode, (result.stdout + result.stderr).strip()

# --- Logger ---
output_log = []

# Helper function to print out loop and append to output file
def log(message: str):
    print(message)
    output_log.append(message)

# --- Loop ---
prompt_text = prompt_file.read_text()

for attempt in range(1, MAX_ATTEMPTS + 1):
    log(f"\n=== Attempt {attempt} ===")

    # Retry the API call up to 3 times before giving up
    for retry in range(3):
        try:
            files, notes = client.prompt(
                prompt=prompt_text,
                attachments=(
                    ([test_file] if INCLUDE_TEST_FILE else []) +
                    ([source_file] if INCLUDE_PREVIOUS_ATTEMPT else [])
                ),
                verbose=False, # don't want my prompt printed everytime 
            )
            break  # API call succeeded, exit retry loop
        except (RuntimeError, ValueError) as e:
            log(f"API error on retry {retry + 1}/3: {e}")
            if retry < 2:
                log("Waiting before retrying...")
                time.sleep(10)
            else:
                log("All retries failed, stopping.")
                OUTPUT_FILE.write_text("\n".join(output_log))
                sys.exit(1)

    code, output = run_tests()
    log(f"Output: {output}")

    if code == 0:
        log(f"\nTests passed on attempt {attempt}.")
        break

    prompt_text += (
        f"\n\n## Attempt {attempt} failed\n"
        f"```\n{output}\n```\n"
        "Fix the failures above. "
        "Do NOT modify the test file. "
        "Do NOT change the constructor signature __init__(self, n, k)."
    )

    time.sleep(30) # Spacing out requests so we don't crash as often

else:
    log(f"\nStopped after {MAX_ATTEMPTS} attempts; tests still failing.")
    OUTPUT_FILE.write_text("\n".join(output_log))
    sys.exit(1)

OUTPUT_FILE.write_text("\n".join(output_log))
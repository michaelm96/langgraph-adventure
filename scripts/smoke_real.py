"""Real-mode smoke test for langgraph-adventure.

Walks each phase's demo with MOCK_LLM=1 unset, using a real MiniMax-M3 call
per LLM invocation. Requires MINIMAX_API_KEY in env or .env file.

Usage:
    # Set the key in your shell:
    export MINIMAX_API_KEY=...
    python scripts/smoke_real.py

    # Or .env file at project root:
    echo 'MINIMAX_API_KEY=...' > .env
    unset MOCK_LLM
    python scripts/smoke_real.py

Caveats:
- Phases 4+ use persistence + interrupts which need a writable ./tmp/.
- Phase 9 (time travel) needs a real checkpointer file.
- Phase 7 (streaming) prints full output, not token-by-token; astream_events
  requires the studio dev server, not a CLI smoke.
- Each phase takes a few seconds and costs ~$0.0003 per call (MiniMax pricing).
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PHASES = [
    ("phase1_stategraph", "minimal turn loop"),
    ("phase2_conditional", "branching scene routing"),
    ("phase3_subgraph", "first NPC interaction"),
    ("phase4_interrupt", "player choice interrupts graph"),
    ("phase5_command", "custom action via Command"),
    ("phase6_send", "two NPCs react in parallel"),
    # phase7_stream skipped — requires studio for token streaming demo
    ("phase8_store", "NPC remembers across sessions"),
    ("phase9_time_travel", "undo last turn"),
]


def main() -> int:
    if os.environ.get("MOCK_LLM") == "1":
        print("ERROR: unset MOCK_LLM first.", file=sys.stderr)
        return 1

    # resolve_model auto-loads .env, so don't pre-check here — let the
    # first phase fail with a friendly RuntimeError if missing.

    # Use a clean tmp dir for persistence so we don't pollute real data.
    tmp = PROJECT_ROOT / "tmp" / "smoke"
    tmp.mkdir(parents=True, exist_ok=True)

    results = []
    for mod, desc in PHASES:
        print(f"\n=== {mod} ({desc}) ===")
        t0 = time.time()
        try:
            cp = subprocess.run(
                [sys.executable, "-m", f"langgraph_adventure.phases.{mod}"],
                cwd=PROJECT_ROOT,
                env={**os.environ, "MOCK_LLM": ""},
                capture_output=True,
                text=True,
                timeout=30,
            )
            elapsed = time.time() - t0
            if cp.returncode == 0:
                print(cp.stdout[-2000:])  # last 2KB
                results.append((mod, "PASS", elapsed))
            else:
                print("STDOUT:", cp.stdout[-500:])
                print("STDERR:", cp.stderr[-1000:])
                results.append((mod, "FAIL", elapsed))
        except subprocess.TimeoutExpired:
            results.append((mod, "TIMEOUT", 30.0))
            print("TIMEOUT after 30s")

    print("\n=== Summary ===")
    for mod, status, elapsed in results:
        print(f"  [{status}] {mod} ({elapsed:.1f}s)")

    failed = [r for r in results if r[1] != "PASS"]
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
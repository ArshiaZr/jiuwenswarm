"""Launch the agent-memory fork's native ingestion API and benchmark barrier.

Usage: python scripts/ingest_memory_benchmark.py --python /path/to/python -- \
    --journal /path/to/journal.db status --job JOB_ID
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent-memory-dir", type=Path,
                        default=Path(__file__).resolve().parents[2] / "agent-memory")
    parser.add_argument("--python", default=sys.executable,
                        help="Python environment with agent-memory and evaluation dependencies")
    args, forwarded = parser.parse_known_args(argv)
    if forwarded[:1] == ["--"]:
        forwarded = forwarded[1:]
    source = args.agent_memory_dir.resolve()
    if not (source / "evaluation/ingestion/__main__.py").is_file():
        parser.error("agent-memory fork with evaluation/ingestion is required")
    environment = os.environ.copy()
    paths = [str(source)]
    if environment.get("PYTHONPATH"):
        paths.append(environment["PYTHONPATH"])
    environment["PYTHONPATH"] = os.pathsep.join(paths)
    return subprocess.run(
        [args.python, "-m", "evaluation.ingestion", *forwarded],
        cwd=source, env=environment, check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())

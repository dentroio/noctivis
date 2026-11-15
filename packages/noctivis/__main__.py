"""Claim queued static-analysis jobs. Pass --once to handle a single job and exit."""

import os
import sys
import time
from pathlib import Path

from noctivis.artifacts import ArtifactStore
from noctivis.store import RecordStore
from noctivis.worker import AnalysisError, run_once


def main() -> int:
    url = os.environ.get("NOCTIVIS_DATABASE_URL", "").strip()
    root = os.environ.get("NOCTIVIS_ARTIFACT_DIR", "").strip()
    if not url or not root:
        print("NOCTIVIS_DATABASE_URL and NOCTIVIS_ARTIFACT_DIR are required", file=sys.stderr)
        return 2
    store = RecordStore(url)
    artifacts = ArtifactStore(Path(root))
    once = "--once" in sys.argv[1:]
    try:
        while True:
            try:
                worked = run_once(store, artifacts)
            except AnalysisError as exc:
                print(str(exc), file=sys.stderr)
                if once:
                    return 1
                continue
            if once or not worked:
                if once:
                    return 0
                time.sleep(2)
    finally:
        store.close()


if __name__ == "__main__":
    raise SystemExit(main())

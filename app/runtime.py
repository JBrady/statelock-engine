from __future__ import annotations

import os
import subprocess
from datetime import datetime, timezone


STARTED_AT = datetime.now(timezone.utc)
CWD = os.getcwd()


def _resolve_git_sha() -> str | None:
    try:
        out = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL)
    except Exception:
        return None
    sha = out.decode("utf-8", errors="ignore").strip()
    return sha or None


GIT_SHA = _resolve_git_sha()

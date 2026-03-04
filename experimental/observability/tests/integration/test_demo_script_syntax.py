from __future__ import annotations

import subprocess


def test_demo_script_bash_syntax():
    result = subprocess.run(["bash", "-n", "scripts/demo_requests.sh"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr

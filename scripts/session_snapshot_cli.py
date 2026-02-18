#!/usr/bin/env python3
"""Export/import StateLock session snapshots over HTTP."""

import argparse
import json
from pathlib import Path

import requests


def export_snapshot(base_url: str, session_id: str, out_file: Path, api_key: str = "") -> None:
    headers = {}
    if api_key:
        headers["X-Statelock-Api-Key"] = api_key
    resp = requests.get(
        f"{base_url.rstrip('/')}/memories/session/{session_id}/snapshot",
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    out_file.write_text(json.dumps(resp.json(), indent=2), encoding="utf-8")


def import_snapshot(
    base_url: str,
    session_id: str,
    in_file: Path,
    mode: str = "append",
    api_key: str = "",
) -> None:
    headers = {"content-type": "application/json"}
    if api_key:
        headers["X-Statelock-Api-Key"] = api_key

    data = json.loads(in_file.read_text(encoding="utf-8"))
    payload = {
        "mode": mode,
        "memories": data.get("memories", []),
    }
    resp = requests.post(
        f"{base_url.rstrip('/')}/memories/session/{session_id}/restore",
        headers=headers,
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()


def main() -> None:
    parser = argparse.ArgumentParser(description="StateLock snapshot import/export helper")
    sub = parser.add_subparsers(dest="cmd", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--base-url", default="http://127.0.0.1:8000")
    common.add_argument("--api-key", default="")

    p_export = sub.add_parser("export", parents=[common])
    p_export.add_argument("--session-id", required=True)
    p_export.add_argument("--out", required=True)

    p_import = sub.add_parser("import", parents=[common])
    p_import.add_argument("--session-id", required=True)
    p_import.add_argument("--in", dest="in_file", required=True)
    p_import.add_argument("--mode", choices=["append", "replace"], default="append")

    args = parser.parse_args()

    if args.cmd == "export":
        export_snapshot(args.base_url, args.session_id, Path(args.out), args.api_key)
    else:
        import_snapshot(args.base_url, args.session_id, Path(args.in_file), args.mode, args.api_key)


if __name__ == "__main__":
    main()

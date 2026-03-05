#!/usr/bin/env python3
"""Minimal real-LLM smoke flow for StateLock Core memory APIs."""

import json
import os
import subprocess
import sys
import textwrap
import time
import traceback
import urllib.error
import urllib.request


def _env(name: str, default: str = "") -> str:
    value = os.getenv(name)
    return value if value is not None else default


def _parse_int(name: str, default: int) -> int:
    raw = _env(name, str(default)).strip()
    try:
        return int(raw)
    except ValueError:
        raise ValueError(f"Invalid integer for {name}: {raw}")


def _parse_float(name: str, default: float) -> float:
    raw = _env(name, str(default)).strip()
    try:
        return float(raw)
    except ValueError:
        raise ValueError(f"Invalid float for {name}: {raw}")


def _parse_bool(name: str, default: bool = False) -> bool:
    raw = _env(name, "1" if default else "0").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _clean_base(url: str) -> str:
    return url.rstrip("/")


def _clean_prefix(prefix: str) -> str:
    p = prefix.strip() or "/memories"
    if not p.startswith("/"):
        p = "/" + p
    return p.rstrip("/")


def _join(base: str, path: str) -> str:
    return _clean_base(base) + "/" + path.lstrip("/")


def _run_cmd(cmd: list[str]) -> str:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        return "(command not found)"
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    return out or err or f"(exit={proc.returncode}, no output)"


def _json_preview(raw: str, limit: int = 500) -> str:
    text = raw.strip().replace("\n", " ")
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def _http_json(
    method: str,
    url: str,
    payload: dict | None = None,
    headers: dict | None = None,
    timeout: int = 60,
) -> tuple[int, dict, str]:
    req_headers: dict[str, str] = dict(headers or {})
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        if not any(k.lower() == "content-type" for k in req_headers):
            req_headers["content-type"] = "application/json"

    req = urllib.request.Request(url=url, data=data, headers=req_headers, method=method.upper())

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.getcode()
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        status = exc.code
        raw = exc.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Request failed for {url}: {exc}") from exc

    try:
        parsed = json.loads(raw) if raw.strip() else {}
        if not isinstance(parsed, dict):
            parsed = {"data": parsed}
    except json.JSONDecodeError:
        parsed = {"raw": raw}

    return status, parsed, raw


def _assert_status(status: int, body: dict, label: str) -> None:
    if 200 <= status < 300:
        return
    raise RuntimeError(f"{label} failed with HTTP {status}: {_json_preview(json.dumps(body, ensure_ascii=False))}")


def _statelock_headers(api_key: str, version_header: str) -> dict[str, str]:
    headers: dict[str, str] = {"content-type": "application/json"}
    if api_key.strip():
        headers["X-Statelock-Api-Key"] = api_key.strip()
    if version_header.strip():
        headers["X-Statelock-Version"] = version_header.strip()
    return headers


def _parse_chat_content(body: dict, raw: str, backend: str) -> str:
    try:
        if backend in {"litellm", "openai"}:
            return str(body["choices"][0]["message"]["content"]).strip()
        if backend == "ollama":
            return str(body["response"]).strip()
    except Exception:
        print(f"[{backend}] parse failure preview: {_json_preview(raw)}")
        if backend in {"litellm", "openai"}:
            raise RuntimeError(f"{backend} parse error: expected choices[0].message.content")
        raise RuntimeError("ollama parse error: expected response")

    print(f"[{backend}] parse failure preview: {_json_preview(raw)}")
    if backend in {"litellm", "openai"}:
        raise RuntimeError(f"{backend} parse error: expected choices[0].message.content")
    raise RuntimeError("ollama parse error: expected response")


def _call_litellm(messages: list[dict], timeout: int) -> dict:
    base = _env("LITELLM_BASE_URL", "http://127.0.0.1:4000")
    model = _env("LITELLM_MODEL", "chat_default").strip() or "chat_default"
    api_key = _env("LITELLM_API_KEY", "").strip()
    headers = {"content-type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    status, body, raw = _http_json(
        "POST",
        _join(base, "/v1/chat/completions"),
        payload={"model": model, "messages": messages, "max_tokens": 300},
        headers=headers,
        timeout=timeout,
    )
    _assert_status(status, body, "LiteLLM chat")
    text = _parse_chat_content(body, raw, "litellm")
    return {"backend": "litellm", "model": model, "text": text}


def _call_ollama(prompt: str, timeout: int) -> dict:
    base = _env("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    model = _env("OLLAMA_MODEL", "qwen2.5:7b-instruct").strip() or "qwen2.5:7b-instruct"

    status, body, raw = _http_json(
        "POST",
        _join(base, "/api/generate"),
        payload={"model": model, "prompt": prompt, "stream": False},
        headers={"content-type": "application/json"},
        timeout=timeout,
    )
    _assert_status(status, body, "Ollama generate")
    text = _parse_chat_content(body, raw, "ollama")
    return {"backend": "ollama", "model": model, "text": text}


def _call_openai(messages: list[dict], timeout: int) -> dict:
    api_key = _env("OPENAI_API_KEY", "").strip()
    model = _env("OPENAI_MODEL", "").strip()
    if not api_key:
        raise RuntimeError("OpenAI backend requested but OPENAI_API_KEY is not set")
    if not model:
        raise RuntimeError("OpenAI backend requested but OPENAI_MODEL is not set")

    base = _env("OPENAI_BASE_URL", "https://api.openai.com/v1")
    headers = {
        "content-type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    status, body, raw = _http_json(
        "POST",
        _join(base, "/chat/completions"),
        payload={"model": model, "messages": messages, "max_tokens": 300},
        headers=headers,
        timeout=timeout,
    )
    _assert_status(status, body, "OpenAI chat")
    text = _parse_chat_content(body, raw, "openai")
    return {"backend": "openai", "model": model, "text": text}


def _call_llm(messages: list[dict], ollama_prompt: str, timeout: int) -> dict:
    mode = _env("LLM_BACKEND", "auto").strip().lower() or "auto"

    if mode == "litellm":
        return _call_litellm(messages, timeout)
    if mode == "ollama":
        return _call_ollama(ollama_prompt, timeout)
    if mode == "openai":
        return _call_openai(messages, timeout)
    if mode != "auto":
        raise RuntimeError("LLM_BACKEND must be one of: auto, litellm, ollama, openai")

    attempts: list[str] = []

    try:
        return _call_litellm(messages, timeout)
    except Exception as exc:
        attempts.append(f"litellm: {exc}")

    try:
        return _call_ollama(ollama_prompt, timeout)
    except Exception as exc:
        attempts.append(f"ollama: {exc}")

    openai_key = _env("OPENAI_API_KEY", "").strip()
    openai_model = _env("OPENAI_MODEL", "").strip()
    if openai_key and openai_model:
        try:
            return _call_openai(messages, timeout)
        except Exception as exc:
            attempts.append(f"openai: {exc}")
    elif openai_key and not openai_model:
        attempts.append("openai: OPENAI_API_KEY is set but OPENAI_MODEL is missing")

    raise RuntimeError("All LLM backends failed in auto mode: " + " | ".join(attempts))


def _preflight_core(base_url: str, timeout: int) -> None:
    health_url = _join(base_url, "/healthz")
    ready_url = _join(base_url, "/readyz")

    health_status, health_body, _ = _http_json("GET", health_url, timeout=timeout)
    ready_status, ready_body, _ = _http_json("GET", ready_url, timeout=timeout)

    print("\n[preflight] /healthz:")
    print(json.dumps({"status": health_status, "body": health_body}, indent=2, ensure_ascii=False))
    print("[preflight] /readyz:")
    print(json.dumps({"status": ready_status, "body": ready_body}, indent=2, ensure_ascii=False))

    if 200 <= health_status < 300 and 200 <= ready_status < 300:
        return

    root_url = _join(base_url, "/")
    root_status, root_body, _ = _http_json("GET", root_url, timeout=timeout)
    print("[preflight] /healthz or /readyz not successful, fallback GET /:")
    print(json.dumps({"status": root_status, "body": root_body}, indent=2, ensure_ascii=False))


def _save_memory(base_url: str, api_prefix: str, timeout: int, content: str) -> dict:
    url = _join(base_url, f"{api_prefix}/")
    name = _env("STATELOCK_MEMORY_NAME", "smoke_turn_1").strip() or "smoke_turn_1"
    session_id = _env("STATELOCK_SESSION_ID", "smoke:local:e2e").strip() or "smoke:local:e2e"
    tags = [t.strip() for t in _env("STATELOCK_TAGS", "smoke,llm,e2e").split(",") if t.strip()]

    payload = {
        "content": content,
        "name": name,
        "session_id": session_id,
        "tags": tags,
    }

    headers = _statelock_headers(
        api_key=_env("STATELOCK_API_KEY", ""),
        version_header=_env("STATELOCK_VERSION_HEADER", ""),
    )

    status, body, _ = _http_json("POST", url, payload=payload, headers=headers, timeout=timeout)
    _assert_status(status, body, "StateLock save")
    return body


def _query_memories(base_url: str, api_prefix: str, timeout: int, query_text: str) -> dict:
    session_id = _env("STATELOCK_SESSION_ID", "smoke:local:e2e").strip()
    top_k = _parse_int("TOP_K", 3)
    use_hybrid = _parse_bool("USE_HYBRID", False)

    payload: dict = {
        "query_text": query_text,
        "session_id": session_id or None,
        "top_k": top_k,
    }
    if use_hybrid:
        payload["candidate_k"] = _parse_int("HYBRID_CANDIDATE_K", 20)
        payload["similarity_weight"] = _parse_float("HYBRID_SIMILARITY_WEIGHT", 0.75)
        payload["recency_weight"] = _parse_float("HYBRID_RECENCY_WEIGHT", 0.25)

    endpoint = "/query-hybrid" if use_hybrid else "/query"
    url = _join(base_url, f"{api_prefix}{endpoint}")
    headers = _statelock_headers(
        api_key=_env("STATELOCK_API_KEY", ""),
        version_header=_env("STATELOCK_VERSION_HEADER", ""),
    )

    status, body, _ = _http_json("POST", url, payload=payload, headers=headers, timeout=timeout)
    _assert_status(status, body, f"StateLock query ({endpoint})")
    return body


def _assemble_context(query_body: dict) -> str:
    results = query_body.get("results", [])
    contents: list[str] = []
    for item in results:
        if isinstance(item, dict):
            content = str(item.get("content", "")).strip()
            if content:
                contents.append(content)

    if not contents:
        return "Memory Context:\n- No prior memory found."

    lines = ["Memory Context:"]
    for text in contents:
        lines.append(f"- {text}")
    return "\n".join(lines)


def _diagnostics(base_url: str, api_prefix: str) -> None:
    print("== Python Diagnostics ==")
    print(f"which python: {_run_cmd(['which', 'python'])}")
    print(f"python -V: {_run_cmd(['python', '-V'])}")
    print(f"sys.executable: {sys.executable}")
    print("\n== Resolved Config ==")
    print(f"STATELOCK_BASE_URL: {base_url}")
    print(f"API_PREFIX: {api_prefix}")


def main() -> int:
    started = time.time()
    try:
        base_url = _clean_base(_env("STATELOCK_BASE_URL", "http://127.0.0.1:8000"))
        api_prefix = _clean_prefix(_env("API_PREFIX", "/memories"))
        timeout = _parse_int("LLM_TIMEOUT_SECONDS", 60)

        turn1_prompt = _env(
            "TURN1_PROMPT",
            "In 2-3 sentences, give a practical tip for staying focused while coding.",
        ).strip()
        turn2_prompt = _env(
            "TURN2_PROMPT",
            "Now give a short follow-up checklist that applies the same advice.",
        ).strip()

        _diagnostics(base_url, api_prefix)
        _preflight_core(base_url, timeout)

        turn1_messages = [{"role": "user", "content": turn1_prompt}]
        turn1_ollama_prompt = turn1_prompt

        turn1 = _call_llm(turn1_messages, turn1_ollama_prompt, timeout)
        print("\n== Turn 1 LLM ==")
        print(json.dumps({"backend": turn1["backend"], "model": turn1["model"]}, indent=2))

        save_body = _save_memory(base_url, api_prefix, timeout, turn1["text"])
        print("\n== Save Response ==")
        print(json.dumps(save_body, indent=2, ensure_ascii=False))
        save_identifier = None
        if isinstance(save_body, dict):
            save_identifier = save_body.get("id") or save_body.get("memory_id")

        query_body = _query_memories(base_url, api_prefix, timeout, turn1_prompt)
        print("\n== Query Response ==")
        print(json.dumps(query_body, indent=2, ensure_ascii=False))

        context_text = _assemble_context(query_body)
        print("\n== Assembled Context ==")
        print(context_text)

        turn2_messages = [
            {"role": "system", "content": "Use the provided memory context when relevant."},
            {"role": "system", "content": context_text},
            {"role": "user", "content": turn2_prompt},
        ]
        turn2_ollama_prompt = textwrap.dedent(
            f"""
            Use the provided memory context when relevant.

            {context_text}

            User request:
            {turn2_prompt}
            """
        ).strip()

        turn2 = _call_llm(turn2_messages, turn2_ollama_prompt, timeout)
        print("\n== Turn 2 LLM ==")
        print(json.dumps({"backend": turn2["backend"], "model": turn2["model"]}, indent=2))

        results = query_body.get("results", []) if isinstance(query_body, dict) else []
        summary = {
            "turn1_backend": turn1["backend"],
            "turn1_model": turn1["model"],
            "turn2_backend": turn2["backend"],
            "turn2_model": turn2["model"],
            "save_identifier": save_identifier,
            "retrieved_count": len(results) if isinstance(results, list) else 0,
            "turn1_preview": turn1["text"][:280],
            "turn2_preview": turn2["text"][:280],
            "elapsed_seconds": round(time.time() - started, 2),
        }

        print("\n== Summary ==")
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0

    except Exception as exc:
        print("\n[error] Smoke flow failed:")
        print(str(exc))
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

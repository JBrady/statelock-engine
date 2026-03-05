#!/usr/bin/env python3
"""Minimal interactive agent loop with StateLock memory sidecar."""

import json
import os
import re
import subprocess
import sys
import textwrap
import traceback
import urllib.error
import urllib.request
from typing import Optional


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
    payload: Optional[dict] = None,
    headers: Optional[dict] = None,
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
    preview = _json_preview(json.dumps(body, ensure_ascii=False))
    raise RuntimeError(f"{label} failed with HTTP {status}: {preview}")


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
        payload={"model": model, "messages": messages, "max_tokens": 500},
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
        payload={"model": model, "messages": messages, "max_tokens": 500},
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

    def probe(url: str) -> tuple[int, dict]:
        try:
            status, body, _ = _http_json("GET", url, timeout=timeout)
            return status, body
        except Exception as exc:
            return 0, {"error": str(exc)}

    health_status, health_body = probe(health_url)
    ready_status, ready_body = probe(ready_url)

    print("\n[preflight] /healthz:")
    print(json.dumps({"status": health_status, "body": health_body}, indent=2, ensure_ascii=False))
    print("[preflight] /readyz:")
    print(json.dumps({"status": ready_status, "body": ready_body}, indent=2, ensure_ascii=False))

    if 200 <= health_status < 300 and 200 <= ready_status < 300:
        return

    root_url = _join(base_url, "/")
    print("[preflight] /healthz or /readyz not successful, fallback GET /:")
    root_status, root_body = probe(root_url)
    print(json.dumps({"status": root_status, "body": root_body}, indent=2, ensure_ascii=False))
    if not (200 <= root_status < 300):
        raise RuntimeError(
            "Core preflight failed: /healthz and /readyz unavailable, fallback GET / also failed"
        )


def _query_memories(base_url: str, api_prefix: str, timeout: int, query_text: str) -> dict:
    session_id = _env("STATELOCK_SESSION_ID", "agent:chat:main").strip()
    top_k = _parse_int("TOP_K", 5)
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


def _save_memory(
    base_url: str,
    api_prefix: str,
    timeout: int,
    content: str,
    name: str,
    tags: list[str],
    session_id: str,
) -> tuple[dict, Optional[str]]:
    url = _join(base_url, f"{api_prefix}/")
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

    save_identifier = None
    if isinstance(body, dict):
        save_identifier = body.get("id") or body.get("memory_id")
    return body, save_identifier


def _normalize_fact_value(raw: str) -> str:
    return re.sub(r"\s+", " ", raw).strip(" \t\"'`.,!?;:")


def _extract_fact_memories(user_text: str) -> list[dict]:
    text = user_text.strip()
    if not text:
        return []

    patterns = [
        (
            re.compile(r"\bmy name is\s+(.+?)(?=(?:\s+\band\b\s+(?:i|my)\b)|[.!?;\n]|$)", re.IGNORECASE),
            "User name is {value}",
            ["fact", "name"],
        ),
        (
            re.compile(r"\bcall me\s+(.+?)(?=(?:\s+\band\b\s+(?:i|my)\b)|[.!?;\n]|$)", re.IGNORECASE),
            "User name is {value}",
            ["fact", "name"],
        ),
        (
            re.compile(r"\bi prefer\s+(.+?)(?=(?:\s+\band\b\s+(?:i|my)\b)|[.!?;\n]|$)", re.IGNORECASE),
            "User prefers {value}",
            ["fact", "preference"],
        ),
    ]

    facts: list[dict] = []
    seen: set[str] = set()
    for pattern, template, tags in patterns:
        for match in pattern.finditer(text):
            value = _normalize_fact_value(match.group(1))
            if not value:
                continue
            content = template.format(value=value)
            dedupe_key = content.lower()
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            facts.append({"content": content, "tags": tags})
    return facts


def _assemble_memory_context(query_body: dict) -> str:
    results = query_body.get("results", []) if isinstance(query_body, dict) else []
    contents: list[str] = []
    for item in results:
        if isinstance(item, dict):
            content = str(item.get("content", "")).strip()
            if content:
                contents.append(content)

    if not contents:
        return "Memory Context:\n- No prior memory found."

    lines = ["Memory Context:"]
    for content in contents:
        lines.append(f"- {content}")
    return "\n".join(lines)


def _build_messages(memory_context: str, user_text: str) -> list[dict]:
    return [
        {"role": "system", "content": "Use the provided memory context when relevant."},
        {"role": "system", "content": memory_context},
        {"role": "user", "content": user_text},
    ]


def _build_ollama_prompt(memory_context: str, user_text: str) -> str:
    return textwrap.dedent(
        f"""
        Use the provided memory context when relevant.

        {memory_context}

        User request:
        {user_text}
        """
    ).strip()


def _should_save_memory(user_text: str, assistant_text: str) -> tuple[bool, str]:
    mode = _env("SAVE_MODE", "always").strip().lower() or "always"

    if mode == "always":
        return True, "always"
    if mode == "never":
        return False, "never"
    if mode != "keyword":
        raise RuntimeError("SAVE_MODE must be one of: always, never, keyword")

    keywords_raw = _env("SAVE_KEYWORDS", "decision,preference,todo,policy")
    keywords = [k.strip().lower() for k in keywords_raw.split(",") if k.strip()]
    combined = f"{user_text}\n{assistant_text}".lower()
    matched = [k for k in keywords if k in combined]
    if matched:
        return True, f"keyword:{','.join(matched)}"
    return False, "keyword:no-match"


def _run_loop(base_url: str, api_prefix: str, timeout: int, session_id: str) -> None:
    turn = 1
    tags_raw = _env("STATELOCK_TAGS", "agent-loop,memory")
    base_tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
    fact_save_enabled = _parse_bool("FACT_SAVE", True)

    print("\nType your message. Type 'exit' or 'quit' to stop.\n")

    while True:
        try:
            user_text = input("You> ").strip()
        except EOFError:
            print("\nEOF received. Exiting.")
            return

        if not user_text:
            continue
        if user_text.lower() in {"exit", "quit"}:
            print("Exiting agent loop.")
            return

        fact_memories = _extract_fact_memories(user_text)
        if fact_memories and fact_save_enabled:
            print(f"[fact-save] extracted={len(fact_memories)}")
            for idx, fact in enumerate(fact_memories, start=1):
                save_name = f"loop_turn_{turn}_fact_{idx}"
                save_tags = base_tags + ["agent-loop"] + fact["tags"]
                save_body, save_id = _save_memory(
                    base_url=base_url,
                    api_prefix=api_prefix,
                    timeout=timeout,
                    content=fact["content"],
                    name=save_name,
                    tags=save_tags,
                    session_id=session_id,
                )
                print("[fact-save] full response:")
                print(json.dumps(save_body, indent=2, ensure_ascii=False))
                print(f"[fact-save] identifier={save_id} content={fact['content']}")
        elif fact_memories:
            print(f"[fact-save] extracted={len(fact_memories)} but FACT_SAVE is disabled")

        query_body = _query_memories(base_url, api_prefix, timeout, user_text)
        results = query_body.get("results", []) if isinstance(query_body, dict) else []
        print(f"[memories] retrieved: {len(results) if isinstance(results, list) else 0}")

        memory_context = _assemble_memory_context(query_body)
        messages = _build_messages(memory_context, user_text)
        ollama_prompt = _build_ollama_prompt(memory_context, user_text)

        llm_out = _call_llm(messages, ollama_prompt, timeout)
        print(f"[llm] backend={llm_out['backend']} model={llm_out['model']}")
        print(f"Assistant> {llm_out['text']}")

        should_save, reason = _should_save_memory(user_text, llm_out["text"])
        print(f"[memory-save] triggered={str(should_save).lower()} reason={reason}")
        if should_save:
            save_name = f"loop_turn_{turn}"
            save_tags = base_tags + ["agent-loop"]
            save_body, save_id = _save_memory(
                base_url=base_url,
                api_prefix=api_prefix,
                timeout=timeout,
                content=llm_out["text"],
                name=save_name,
                tags=save_tags,
                session_id=session_id,
            )
            print("[memory-save] full response:")
            print(json.dumps(save_body, indent=2, ensure_ascii=False))
            print(f"[memory-save] identifier={save_id}")

        turn += 1
        print()


def main() -> int:
    try:
        base_url = _clean_base(_env("STATELOCK_BASE_URL", "http://127.0.0.1:8000"))
        api_prefix = _clean_prefix(_env("API_PREFIX", "/memories"))
        session_id = _env("STATELOCK_SESSION_ID", "agent:chat:main").strip() or "agent:chat:main"
        timeout = _parse_int("LLM_TIMEOUT_SECONDS", 60)
        top_k = _parse_int("TOP_K", 5)
        llm_backend = _env("LLM_BACKEND", "auto").strip() or "auto"
        save_mode = _env("SAVE_MODE", "always").strip() or "always"
        fact_save = _parse_bool("FACT_SAVE", True)

        print("== Python Diagnostics ==")
        print(f"which python: {_run_cmd(['which', 'python'])}")
        print(f"python -V: {_run_cmd(['python', '-V'])}")
        print(f"sys.executable: {sys.executable}")

        print("\n== Resolved Config ==")
        print(f"STATELOCK_BASE_URL: {base_url}")
        print(f"API_PREFIX: {api_prefix}")
        print(f"STATELOCK_SESSION_ID: {session_id}")
        print(f"TOP_K: {top_k}")
        print(f"LLM_BACKEND: {llm_backend}")
        print(f"SAVE_MODE: {save_mode}")
        print(f"FACT_SAVE: {str(fact_save).lower()}")

        _preflight_core(base_url, timeout)
        _run_loop(base_url, api_prefix, timeout, session_id)
        return 0

    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")
        return 130
    except Exception as exc:
        print("\n[error] Agent loop failed:")
        print(str(exc))
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

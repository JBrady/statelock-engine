# Local LLM Stack

This document explains the surrounding local-first stack that StateLock commonly
runs alongside.

## System Architecture

Components:

- Ollama
  - runs local models
  - default port: `11434`
  - used by Ollama UI and LiteLLM
- LiteLLM
  - proxy router
  - default port: `4000`
  - exposes an OpenAI-style API
  - routes to local Ollama models or configured cloud models
- StateLock
  - memory and continuity system
  - does not route model calls
  - can be used alongside LiteLLM-based agents and clients

StateLock sits beside LiteLLM in this stack:

- model calls go to LiteLLM
- memory/continuity calls go to StateLock

## Port Overview

- `11434` = Ollama local model runtime
- `3000` = Ollama Web UI
- `4000` = LiteLLM proxy
- `8000` = StateLock Core
- `8001` = StateLock Observability when launched from repo root
- `3001` = StateLock unified web UI when launched from repo root

## Normal Usage

Casual local chat:

- open `http://localhost:3000`
- this talks directly to Ollama
- LiteLLM is not required

Programmatic agent/model calls:

- call `http://localhost:4000/v1/chat/completions`
- this goes through LiteLLM and can route local-first with optional cloud fallback

StateLock usage:

- call StateLock Core for memory APIs such as `/memories/*`
- optionally call StateLock Observability for `/v2/*` continuity and telemetry APIs
- StateLock itself remains separate from model routing

## Starting Services

Check whether Ollama is running:

```bash
lsof -i :11434
```

If it is not running:

```bash
ollama serve
```

Start LiteLLM in the foreground:

```bash
~/venvs/litellm/bin/litellm --config ~/litellm.yaml --port 4000
```

Start LiteLLM in the background:

```bash
nohup ~/venvs/litellm/bin/litellm --config ~/litellm.yaml --port 4000 > ~/litellm.log 2>&1 &
```

Start the StateLock repo-local stack after the repo environments are set up:

```bash
make dev-up
```

Useful repo-root companion commands:

```bash
make dev-status
make dev-logs
make dev-down
```

## Stop LiteLLM

Check which process owns port `4000`:

```bash
lsof -i :4000
```

Kill a specific process:

```bash
kill PID_NUMBER
```

Kill all LiteLLM instances:

```bash
pkill -f litellm
```

## Verify LiteLLM Is Running

Check available models:

```bash
curl -s http://localhost:4000/v1/models | python3 -c 'import sys, json; data = json.load(sys.stdin); print([m["id"] for m in data["data"]])'
```

Typical output:

```text
['chat_default', 'deep_default', 'code_default', 'cloud_code', 'cloud_reason']
```

## Test Chat Through LiteLLM

```bash
curl -s http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"chat_default","messages":[{"role":"user","content":"Say: banana"}],"max_tokens":20}'
```

## Model Config File

Typical location:

- `~/litellm.yaml`

Example aliases:

- local
  - `chat_default`
  - `deep_default`
  - `code_default`
- cloud
  - `cloud_code`
  - `cloud_reason`

Exact model mappings depend on your local `litellm.yaml`.

## Mental Model

- Ollama = model engine
- LiteLLM = model switchboard/router
- StateLock = memory/continuity sidecar

Ollama UI bypasses LiteLLM completely.

## When To Run LiteLLM

Run it when:

- developing or testing LiteLLM-routed model flows
- building agents or client apps that call `/v1/chat/completions`
- using fallback logic across local and cloud models

Do not run it when:

- you are just chatting in Ollama UI
- you are only working on StateLock memory APIs without any model-calling client flow

## OpenAI Key Setup

Only required when LiteLLM is configured to call cloud models:

```bash
echo 'export OPENAI_API_KEY="YOUR_KEY"' >> ~/.zshrc
source ~/.zshrc
```

## Clean Restart

```bash
pkill -f litellm && ~/venvs/litellm/bin/litellm --config ~/litellm.yaml --port 4000
```

## Canonical Repo Location

The canonical repo path used throughout the current docs is:

- `~/projects/statelock-engine`

Legacy client example:

- `examples/statelock-seed-client/`

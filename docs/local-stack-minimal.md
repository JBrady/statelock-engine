# Local Stack Minimal Cheat Sheet

Only the commands you actually need.

## Start Work Session

1. Make sure Ollama is running:

```bash
lsof -i :11434
```

If nothing is listening:

```bash
ollama serve
```

2. Start LiteLLM only when you need routed model calls:

```bash
~/venvs/litellm/bin/litellm --config ~/litellm.yaml --port 4000
```

Background mode:

```bash
nohup ~/venvs/litellm/bin/litellm --config ~/litellm.yaml --port 4000 > ~/litellm.log 2>&1 &
```

3. Start the repo-local StateLock stack when needed:

```bash
make dev-up
```

## Stop LiteLLM

```bash
pkill -f litellm
lsof -i :4000
```

## Verify LiteLLM

```bash
curl -s http://localhost:4000/v1/models | python3 -c 'import sys, json; data = json.load(sys.stdin); print([m["id"] for m in data["data"]])'
```

## Test a Local Model Through LiteLLM

```bash
curl -s http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"chat_default","messages":[{"role":"user","content":"Say: ok"}],"max_tokens":10}'
```

## Chat Interface

Local-only chat UI:

- `http://localhost:3000`

## Remember

- Ollama = local engine
- LiteLLM = router
- StateLock = separate memory/continuity sidecar

If you are just chatting in Ollama UI, you do not need LiteLLM running.

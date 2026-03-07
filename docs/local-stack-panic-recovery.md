# Local Stack Panic Recovery Checklist

Do these in order. Do not skip steps.

## Step 1: What Is Actually Broken?

Ask yourself:

Are you:

- Just chatting in the browser?
- Running StateLock / `client.ts`?
- Getting a 500 error?
- Getting connection refused?

Different problems = different fixes.

## Step 2: Check Ollama

Check if Ollama is alive:

```bash
lsof -i :11434
```

If nothing shows:

```bash
ollama serve
```

Test Ollama directly:

```bash
curl http://localhost:11434/api/generate -d '{"model":"qwen2.5:7b-instruct","prompt":"say ok","stream":false}'
```

If that works -> Ollama is fine.

Do NOT reinstall Ollama.

## Step 3: Check LiteLLM

Check if running:

```bash
lsof -i :4000
```

If nothing shows:

```bash
~/venvs/litellm/bin/litellm --config ~/litellm.yaml --port 4000
```

If multiple instances:

```bash
pkill -f litellm
```

Start again clean.

## Step 4: Verify Models

```bash
curl -s http://localhost:4000/v1/models
```

If you see:

- `chat_default`
- `deep_default`
- `code_default`
- `cloud_code`
- `cloud_reason`

LiteLLM config is loading correctly.

If not -> check `~/litellm.yaml` exists.

## Step 5: Test Simple Call

```bash
curl -s http://localhost:4000/v1/chat/completions -H "Content-Type: application/json" -d '{"model":"chat_default","messages":[{"role":"user","content":"say ok"}],"max_tokens":10}'
```

If that works -> routing works.

If that fails:

- Read the error carefully.
- It is almost always auth or model name mismatch.
- Do not reinstall Python.

## Step 6: Cloud Error?

If you see:

- `AuthenticationError`
- or `OPENAI_API_KEY` errors

Fix:

```bash
echo 'export OPENAI_API_KEY="YOUR_KEY"' >> ~/.zshrc
source ~/.zshrc
```

Do NOT touch Ollama.

## Step 7: UI Confusion?

Remember:

- Port `3000` = Ollama UI = local only
- Port `4000` = LiteLLM = router

The UI does NOT use LiteLLM.

## Never Do This During Panic

Do NOT:

- Delete venv
- Reinstall Python
- Reinstall Ollama
- Randomly upgrade pip
- Install random dependencies
- Change model names blindly

## If Still Broken

Run these and inspect:

```bash
lsof -i :11434
lsof -i :4000
cat ~/litellm.yaml
which litellm
```

Then debug calmly.

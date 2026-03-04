LOCAL STACK PANIC RECOVERY CHECKLIST
Do these in order. Do not skip steps.

⸻

STEP 1 — WHAT IS ACTUALLY BROKEN?

Ask yourself:

Are you:
	•	Just chatting in the browser?
	•	Running StateLock / client.ts?
	•	Getting a 500 error?
	•	Getting connection refused?

Different problems = different fixes.

⸻

STEP 2 — CHECK OLLAMA

Check if Ollama is alive:

lsof -i :11434

If nothing shows:
ollama serve

Test Ollama directly:

curl http://localhost:11434/api/generate -d ‘{“model”:“qwen2.5:7b-instruct”,“prompt”:“say ok”,“stream”:false}’

If that works → Ollama is fine.

Do NOT reinstall Ollama.

⸻

STEP 3 — CHECK LITELLM

Check if running:

lsof -i :4000

If nothing shows:
~/venvs/litellm/bin/litellm –config ~/litellm.yaml –port 4000

If multiple instances:
pkill -f litellm
Start again clean.

⸻

STEP 4 — VERIFY MODELS

curl -s http://localhost:4000/v1/models

If you see:
chat_default
deep_default
code_default
cloud_code
cloud_reason

LiteLLM config is loading correctly.

If not → check ~/litellm.yaml exists.

⸻

STEP 5 — TEST SIMPLE CALL

curl -s http://localhost:4000/v1/chat/completions -H “Content-Type: application/json” -d ‘{“model”:“chat_default”,“messages”:[{“role”:“user”,“content”:“say ok”}],“max_tokens”:10}’

If that works → routing works.

If that fails:
	•	Read the error carefully.
	•	It is almost always auth or model name mismatch.
	•	Do not reinstall Python.

⸻

STEP 6 — CLOUD ERROR?

If you see:
AuthenticationError
or OPENAI_API_KEY errors

Fix:
echo ‘export OPENAI_API_KEY=“YOUR_KEY”’ >> ~/.zshrc
source ~/.zshrc

Do NOT touch Ollama.

⸻

STEP 7 — UI CONFUSION?

Remember:

Port 3000 = Ollama UI = local only
Port 4000 = LiteLLM = router

The UI does NOT use LiteLLM.

⸻

NEVER DO THIS DURING PANIC

Do NOT:
	•	Delete venv
	•	Reinstall Python
	•	Reinstall Ollama
	•	Randomly upgrade pip
	•	Install random dependencies
	•	Change model names blindly

⸻

IF STILL BROKEN

Run these and inspect:

lsof -i :11434
lsof -i :4000
cat ~/litellm.yaml
which litellm

Then debug calmly.


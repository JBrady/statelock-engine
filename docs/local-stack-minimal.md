LOCAL STACK MINIMAL CHEAT SHEET
Only the commands you actually need

⸻

START WORK SESSION
	1.	Make sure Ollama is running

Check:
lsof -i :11434

If nothing shows:
ollama serve
	2.	Start LiteLLM (only if building StateLock or agents)

~/venvs/litellm/bin/litellm –config ~/litellm.yaml –port 4000

If you want it in background:
nohup ~/venvs/litellm/bin/litellm –config ~/litellm.yaml –port 4000 > ~/litellm.log 2>&1 &

⸻

STOP LITELLM

Kill all instances:
pkill -f litellm

Confirm:
lsof -i :4000

⸻

VERIFY LITELLM IS WORKING

Check models:
curl -s http://localhost:4000/v1/models | python3 -c ‘import sys,json; d=json.load(sys.stdin); print([m[“id”] for m in d[“data”]])’

⸻

TEST LOCAL MODEL THROUGH LITELLM

curl -s http://localhost:4000/v1/chat/completions -H “Content-Type: application/json” -d ‘{“model”:“chat_default”,“messages”:[{“role”:“user”,“content”:“Say: ok”}],“max_tokens”:10}’

⸻

CHAT INTERFACE

Local-only chat:
http://localhost:3000

⸻

REMEMBER

Ollama = local engine
LiteLLM = router
StateLock = always talks to LiteLLM

If you are just chatting, you do NOT need LiteLLM running.

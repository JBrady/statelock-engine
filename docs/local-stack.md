LOCAL LLM STACK DOCUMENTATION
Mac Mini M4 · Ollama · LiteLLM · StateLock

⸻

	1.	SYSTEM ARCHITECTURE

Components

Ollama
	•	Runs local models
	•	Port: 11434
	•	Used by Ollama UI and LiteLLM

LiteLLM
	•	Proxy router
	•	Port: 4000
	•	Provides OpenAI-style API
	•	Routes to local (Ollama) or cloud (OpenAI)

StateLock
	•	Will talk only to LiteLLM
	•	Never directly to Ollama or OpenAI

⸻

	2.	PORT OVERVIEW

11434 = Ollama (local models)
3000  = Ollama Web UI
4000  = LiteLLM proxy

⸻

	3.	NORMAL USAGE

Casual Chat
Open browser: http://localhost:3000
This is 100 percent local. No LiteLLM involved.

Programmatic / Agents
Call: http://localhost:4000/v1/chat/completions
This goes through LiteLLM and can route local first, cloud fallback.

⸻

	4.	STARTING SERVICES

Check if Ollama is running
lsof -i :11434

If not running
ollama serve

Start LiteLLM (foreground)
~/venvs/litellm/bin/litellm –config ~/litellm.yaml –port 4000

Start LiteLLM (background)
nohup ~/venvs/litellm/bin/litellm –config ~/litellm.yaml –port 4000 > ~/litellm.log 2>&1 &

⸻

	5.	STOP LITELLM

Check
lsof -i :4000

Kill specific process
kill PID_NUMBER

Kill all LiteLLM instances
pkill -f litellm

⸻

	6.	VERIFY LITELLM IS RUNNING

Check models
curl -s http://localhost:4000/v1/models | python3 -c ‘import sys,json; d=json.load(sys.stdin); print([m[“id”] for m in d[“data”]])’

Expected output
[‘chat_default’, ‘deep_default’, ‘code_default’, ‘cloud_code’, ‘cloud_reason’]

⸻

	7.	TEST CHAT THROUGH LITELLM

curl -s http://localhost:4000/v1/chat/completions -H “Content-Type: application/json” -d ‘{“model”:“chat_default”,“messages”:[{“role”:“user”,“content”:“Say: banana”}],“max_tokens”:20}’

⸻

	8.	MODEL CONFIG FILE

Location
~/litellm.yaml

Local models
chat_default → qwen2.5 7B
deep_default → qwen2.5 14B
code_default → qwen2.5-coder 7B

Cloud models
cloud_code → gpt-5.2-codex
cloud_reason → gpt-5.2-chat-latest

Guardrails disabled.

⸻

	9.	MENTAL MODEL

Ollama = engine
LiteLLM = switchboard
StateLock = system using switchboard

Ollama UI bypasses LiteLLM completely.

StateLock must always use LiteLLM.

⸻

	10.	WHEN TO RUN LITELLM

Run it when
	•	Developing StateLock
	•	Testing routing
	•	Using fallback logic
	•	Building agents

Do not run it when
	•	Just chatting locally
	•	Not building

⸻

	11.	OPENAI KEY SETUP

Add to shell
echo ‘export OPENAI_API_KEY=“YOUR_KEY”’ >> ~/.zshrc
source ~/.zshrc

Only used when cloud models are called.

⸻

	12.	CLEAN RESTART

pkill -f litellm && ~/venvs/litellm/bin/litellm –config ~/litellm.yaml –port 4000

⸻

	13.	STATELOCK PROJECT LOCATION

~/projects/statelock-seed

Run client
npx tsx src/client.ts “Your prompt”


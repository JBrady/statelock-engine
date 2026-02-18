# OpenClaw Runtime Bundle (Memory Commands)

This folder exports the working OpenClaw runtime artifacts for StateLock memory commands.

It includes:

- plugin tool: `extensions/memory_query_tool/`
- skills: `skills/memory_query/` and `skills/memory_save/`
- config snippet: `config-snippets/openclaw.memory-tools.snippet.json`

## Install (host machine)

1. Copy plugin files:

```bash
mkdir -p ~/.openclaw/extensions/memory_query_tool
cp examples/openclaw-tooling/openclaw-runtime/extensions/memory_query_tool/* ~/.openclaw/extensions/memory_query_tool/
```

2. Copy skill files:

```bash
mkdir -p ~/.openclaw/workspace/skills/memory_query ~/.openclaw/workspace/skills/memory_save
cp examples/openclaw-tooling/openclaw-runtime/skills/memory_query/SKILL.md ~/.openclaw/workspace/skills/memory_query/SKILL.md
cp examples/openclaw-tooling/openclaw-runtime/skills/memory_save/SKILL.md ~/.openclaw/workspace/skills/memory_save/SKILL.md
```

3. Merge config keys into `~/.openclaw/openclaw.json` and `~/.openclaw-cli/openclaw.json`:

- `plugins.entries.memory_query_tool`
- `channels.telegram.customCommands` adds `memory_query` + `memory_save`

Reference snippet:

- `config-snippets/openclaw.memory-tools.snippet.json`

4. Restart OpenClaw gateway.

## Telegram usage

- Query memory:
  - `/memory_query cloud fallback`
- Save memory (plain):
  - `/memory_save We use local first and escalate when confidence is low.`
- Save memory with metadata (Telegram-safe JSON):
  - `/memory_save {"content":"Cloud fallback for low-confidence answers","name":"fallback policy","tags":"policy,fallback"}`

## Notes

- Defaults to `session_id = agent:chat:main` unless you pass `session_id` in JSON mode.
- JSON array tags can be mangled by Telegram slash command parsing; use comma string tags for reliability.

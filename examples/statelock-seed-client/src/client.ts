type Msg = { role: "system" | "user" | "assistant"; content: string };

const BASE_URL = "http://localhost:4000";

// Models exposed by your LiteLLM /v1/models
const MODEL_CHAT_LOCAL = "chat_default";  // local qwen 7b instruct
const MODEL_DEEP_LOCAL = "deep_default";  // local qwen 14b instruct
const MODEL_CODE_CLOUD = "cloud_code";    // openai/gpt-5.2-codex (needs OPENAI_API_KEY)

async function callChat(
  baseUrl: string,
  model: string,
  messages: Msg[],
  timeoutMs: number,
  maxTokens = 400
) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), timeoutMs);

  try {
    const res = await fetch(`${baseUrl}/v1/chat/completions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model, messages, max_tokens: maxTokens }),
      signal: ctrl.signal,
    });

    const text = await res.text();
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${text}`);

    const json = JSON.parse(text);
    const out = (json?.choices?.[0]?.message?.content ?? "").trim();
    return { json, out, model };
  } finally {
    clearTimeout(t);
  }
}

function looksBad(out: string) {
  if (!out) return true;
  if (out.length < 20) return true;
  if (/^i (can'?t|cannot)|as an ai/i.test(out)) return true;
  // common “stall” / non-answer patterns
  if (/^(sure|certainly)[\s\S]*\bhere'?s\b/i.test(out) && out.length < 80) return true;
  return false;
}

function isCodeIntent(messages: Msg[]) {
  const lastUser = [...messages].reverse().find(m => m.role === "user")?.content ?? "";
  return /\b(typescript|javascript|node|npm|tsconfig|eslint|vitest|jest|react|next\.js|express|fastapi|sql|schema|api|endpoint|implement|write (a|the) (function|class)|refactor|bug|stack trace|error|compile|typecheck|unit test)\b/i.test(
    lastUser
  );
}

export async function chat(messages: Msg[]) {
  const wantsCode = isCodeIntent(messages);

  // If user wants code, go straight to cloud_code by default
  if (wantsCode) {
    return await callChat(BASE_URL, MODEL_CODE_CLOUD, messages, 120_000, 700);
  }

  // Otherwise: local chat first, fallback to "deep" local, then cloud_code (optional)
  try {
    const r1 = await callChat(BASE_URL, MODEL_CHAT_LOCAL, messages, 45_000, 500);
    if (!looksBad(r1.out)) return r1;
    throw new Error("Local chat output looks bad");
  } catch {
    try {
      const r2 = await callChat(BASE_URL, MODEL_DEEP_LOCAL, messages, 90_000, 700);
      if (!looksBad(r2.out)) return r2;
      throw new Error("Deep local output looks bad");
    } catch {
      // last resort: cloud code model (works fine for normal chat too)
      return await callChat(BASE_URL, MODEL_CODE_CLOUD, messages, 120_000, 700);
    }
  }
}

// quick CLI run
// tsx runs ESM, so top-level await is fine in your setup ("type": "module")
if (import.meta.url === `file://${process.argv[1]}`) {
  const prompt = process.argv.slice(2).join(" ") || "Say hi in 1 sentence.";
  const r = await chat([{ role: "user", content: prompt }]);
  console.log(`[model=${r.model}] ${r.out}`);
}
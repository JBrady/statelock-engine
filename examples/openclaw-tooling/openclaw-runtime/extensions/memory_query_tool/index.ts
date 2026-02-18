const DEFAULT_QUERY_ENDPOINTS = [
  "http://host.docker.internal:8000/memories/query-hybrid",
  "http://127.0.0.1:8000/memories/query-hybrid",
  "http://localhost:8000/memories/query-hybrid"
];

const DEFAULT_SAVE_ENDPOINTS = [
  "http://host.docker.internal:8000/memories/",
  "http://127.0.0.1:8000/memories/",
  "http://localhost:8000/memories/"
];

function getPluginConfig(api: any): {
  endpoint?: string;
  saveEndpoint?: string;
  sessionId?: string;
  failOpen?: boolean;
  apiKey?: string;
} {
  const entries = api?.config?.plugins?.entries;
  const cfg = entries && entries.memory_query_tool && entries.memory_query_tool.config;
  return cfg && typeof cfg === "object" ? cfg : {};
}

async function postJson(
  url: string,
  payload: Record<string, unknown>,
  timeoutMs = 5000,
  apiKey?: string
) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        ...(apiKey ? { "X-Statelock-Api-Key": apiKey } : {})
      },
      body: JSON.stringify(payload),
      signal: controller.signal
    });
  } finally {
    clearTimeout(timer);
  }
}

function normalizeTags(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value
      .map((v) => String(v).trim())
      .filter((v) => v.length > 0);
  }
  if (typeof value === "string") {
    return value
      .split(",")
      .map((v) => v.trim())
      .filter((v) => v.length > 0);
  }
  return [];
}

function deriveSessionId(args: any, configuredSessionId?: string): string {
  const fallback = (configuredSessionId || "agent:chat:main").trim();
  const channel = String(
    args?.channel || args?.source || args?.platform || ""
  ).trim();
  const chatOrThread = String(
    args?.thread || args?.thread_id || args?.chat || args?.chat_id || ""
  ).trim();
  const userOrAgent = String(
    args?.user || args?.user_id || args?.agent || args?.agent_id || ""
  ).trim();
  if (channel && chatOrThread && userOrAgent) {
    return `${channel}:${chatOrThread}:${userOrAgent}`;
  }
  return fallback;
}

function signalConfidence(modelOutput: string): { confidence_low: boolean; reason: string } {
  const text = modelOutput.trim();
  if (!text) {
    return { confidence_low: true, reason: "empty_response" };
  }
  const uncertainty = /\b(i am not sure|i think|maybe|might|uncertain|not confident)\b/i.test(text);
  if (uncertainty) {
    return { confidence_low: true, reason: "uncertainty_language" };
  }
  if (text.split(/\s+/).length < 8) {
    return { confidence_low: true, reason: "too_short" };
  }
  return { confidence_low: false, reason: "none" };
}

function maybeParseJson(raw: string): any | null {
  const trimmed = raw.trim();
  if (!(trimmed.startsWith("{") && trimmed.endsWith("}"))) {
    return null;
  }
  return JSON.parse(trimmed);
}

function parseMemorySaveCommand(
  raw: string,
  defaults: { sessionId: string }
): { content: string; name: string; tags: string[]; session_id: string; model_output?: string } {
  const trimmed = raw.trim();
  if (trimmed.startsWith("{") && trimmed.endsWith("}")) {
    let parsed: any = null;
    try {
      parsed = JSON.parse(trimmed);
    } catch {
      // Telegram slash command payloads can mangle brackets/quotes.
      // Fall back to a permissive key extractor for common fields.
      const contentMatch = trimmed.match(/"content"\s*:\s*"([^"]*)"/);
      const nameMatch = trimmed.match(/"name"\s*:\s*"([^"]*)"/);
      const sessionMatch = trimmed.match(/"session_id"\s*:\s*"([^"]*)"/);
      const tagsArrayMatch = trimmed.match(/"tags"\s*:\s*\[([^\]]*)\]/);
      const tagsStringMatch = trimmed.match(/"tags"\s*:\s*"([^"]*)"/);

      if (!contentMatch?.[1]) {
        throw new Error("memory_save JSON requires non-empty 'content'.");
      }

      let tags: string[] = [];
      if (tagsArrayMatch?.[1]) {
        tags = tagsArrayMatch[1]
          .split(",")
          .map((v) => v.replace(/['"]/g, "").trim())
          .filter((v) => v.length > 0);
      } else if (tagsStringMatch?.[1]) {
        tags = normalizeTags(tagsStringMatch[1]);
      }

      return {
        content: contentMatch[1].trim(),
        name: (nameMatch?.[1] || "telegram memory").trim() || "telegram memory",
        tags: tags.length > 0 ? tags : ["telegram", "manual"],
        session_id: (sessionMatch?.[1] || defaults.sessionId).trim() || defaults.sessionId,
        model_output: undefined
      };
    }

    if (!parsed || typeof parsed !== "object") {
      throw new Error("memory_save JSON must be an object.");
    }
    const content = String((parsed as any).content ?? "").trim();
    if (!content) {
      throw new Error("memory_save JSON requires non-empty 'content'.");
    }
    const name = String((parsed as any).name ?? "telegram memory").trim() || "telegram memory";
    const tags = normalizeTags((parsed as any).tags);
    const sessionId = String((parsed as any).session_id ?? defaults.sessionId).trim() || defaults.sessionId;
    return {
      content,
      name,
      tags: tags.length > 0 ? tags : ["telegram", "manual"],
      session_id: sessionId,
      model_output: typeof (parsed as any).model_output === "string" ? (parsed as any).model_output : undefined
    };
  }

  return {
    content: trimmed,
    name: "telegram memory",
    tags: ["telegram", "manual"],
    session_id: defaults.sessionId,
    model_output: undefined
  };
}

function parseMemoryQueryCommand(
  raw: string,
  defaults: { sessionId: string }
): {
  query_text: string;
  session_id: string;
  top_k: number;
  candidate_k: number;
  similarity_weight: number;
  recency_weight: number;
} {
  const parsed = maybeParseJson(raw);
  if (!parsed || typeof parsed !== "object") {
    return {
      query_text: raw.trim(),
      session_id: defaults.sessionId,
      top_k: 5,
      candidate_k: 20,
      similarity_weight: 0.75,
      recency_weight: 0.25
    };
  }
  const queryText = String(parsed.query || parsed.query_text || "").trim();
  if (!queryText) {
    throw new Error("memory.query requires non-empty 'query' or 'query_text'.");
  }
  return {
    query_text: queryText,
    session_id: String(parsed.session_id || defaults.sessionId).trim() || defaults.sessionId,
    top_k: Number(parsed.top_k || 5),
    candidate_k: Number(parsed.candidate_k || 20),
    similarity_weight: Number(parsed.similarity_weight ?? 0.75),
    recency_weight: Number(parsed.recency_weight ?? 0.25)
  };
}

export default function register(api: any) {
  api.registerTool({
    name: "memory_query_tool",
    label: "Memory Query",
    description: "Query StateLock memory by query text and return JSON results.",
    parameters: {
      type: "object",
      additionalProperties: true,
      properties: {
        command: { type: "string", description: "Memory query text." },
        commandName: { type: "string" },
        skillName: { type: "string" }
      },
      required: ["command"]
    },
    async execute(_toolCallId: string, args: any) {
      const queryText = String(args?.command ?? "").trim();
      if (!queryText) {
        throw new Error("memory_query_tool requires query text.");
      }

      const cfg = getPluginConfig(api);
      const failOpen = cfg.failOpen !== false;
      const endpoints = [cfg.endpoint, process.env.STATELOCK_ENDPOINT, ...DEFAULT_QUERY_ENDPOINTS]
        .filter((v): v is string => typeof v === "string" && v.trim().length > 0);

      const sessionId = deriveSessionId(args, cfg.sessionId);
      const payload = parseMemoryQueryCommand(queryText, { sessionId });

      let lastError = "";
      for (const endpoint of endpoints) {
        try {
          const resp = await postJson(endpoint, payload, 5000, cfg.apiKey);
          const text = await resp.text();
          if (!resp.ok) {
            lastError = `${endpoint} -> HTTP ${resp.status}: ${text}`;
            continue;
          }
          return {
            content: [{ type: "text", text }]
          };
        } catch (err: any) {
          lastError = `${endpoint} -> ${String(err?.message || err)}`;
        }
      }

      if (failOpen) {
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({
                results: [],
                warning: "memory_unavailable",
                details: lastError
              })
            }
          ]
        };
      }
      throw new Error(`StateLock query failed. ${lastError}`);
    }
  });

  api.registerTool({
    name: "memory_save_tool",
    label: "Memory Save",
    description: "Save memory text to StateLock and return JSON result.",
    parameters: {
      type: "object",
      additionalProperties: true,
      properties: {
        command: { type: "string", description: "Memory text to store." },
        commandName: { type: "string" },
        skillName: { type: "string" }
      },
      required: ["command"]
    },
    async execute(_toolCallId: string, args: any) {
      const content = String(args?.command ?? "").trim();
      if (!content) {
        throw new Error("memory_save_tool requires memory text.");
      }

      const cfg = getPluginConfig(api);
      const failOpen = cfg.failOpen !== false;
      const endpoints = [cfg.saveEndpoint, process.env.STATELOCK_SAVE_ENDPOINT, ...DEFAULT_SAVE_ENDPOINTS]
        .filter((v): v is string => typeof v === "string" && v.trim().length > 0);

      let payload: { content: string; name: string; session_id: string; tags: string[]; model_output?: string };
      try {
        payload = parseMemorySaveCommand(content, {
          sessionId: deriveSessionId(args, cfg.sessionId)
        });
      } catch (err: any) {
        throw new Error(
          `Invalid /memory_save format. Use plain text or JSON like {"content":"...","name":"...","tags":["a","b"]}. ${String(err?.message || err)}`
        );
      }
      const confidence = signalConfidence(payload.model_output || "");
      const savePayload = {
        content: payload.content,
        name: payload.name,
        session_id: payload.session_id,
        tags: payload.tags
      };

      let lastError = "";
      for (const endpoint of endpoints) {
        try {
          const resp = await postJson(endpoint, savePayload, 5000, cfg.apiKey);
          const text = await resp.text();
          if (!resp.ok) {
            lastError = `${endpoint} -> HTTP ${resp.status}: ${text}`;
            continue;
          }
          let parsed: any = {};
          try {
            parsed = JSON.parse(text);
          } catch {
            parsed = { raw: text };
          }
          return {
            content: [
              {
                type: "text",
                text: JSON.stringify({
                  ...parsed,
                  confidence_low: confidence.confidence_low,
                  confidence_reason: confidence.reason
                })
              }
            ]
          };
        } catch (err: any) {
          lastError = `${endpoint} -> ${String(err?.message || err)}`;
        }
      }

      if (failOpen) {
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({
                saved: false,
                warning: "memory_unavailable",
                details: lastError,
                confidence_low: confidence.confidence_low,
                confidence_reason: confidence.reason
              })
            }
          ]
        };
      }
      throw new Error(`StateLock save failed. ${lastError}`);
    }
  });
}

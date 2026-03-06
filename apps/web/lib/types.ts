export type ProxyHeaders = Record<string, string | null>;

export type ProxyPayload<T = unknown> = {
  ok: boolean;
  status: number;
  headers: ProxyHeaders;
  data: T;
};

export type CoreStats = {
  total_memories: number;
  total_sessions: number;
  recent_writes_24h: number;
  top_tags: Array<{ tag: string; count: number }>;
};

export type CoreSession = {
  session_id: string;
  memory_count: number;
  last_updated?: string | null;
};

export type CoreMemory = {
  id: string;
  content: string;
  name?: string | null;
  session_id: string;
  tags: string[];
  created_at?: string | null;
  updated_at?: string | null;
  distance?: number | null;
  score?: number | null;
};

export type ObservabilityConversation = {
  conversation_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  settings: {
    max_context_tokens: number;
    telemetry_mode: string;
    target_thread_mode: string;
    pinned_thread_id?: string | null;
  };
};

export type ObservabilityRunGroup = {
  run_group_id: string;
  created_at_min?: string;
  created_at_max?: string;
  turn_id?: string;
  target_thread_id?: string;
  has_proxy?: boolean;
  has_ablation?: boolean;
  Coff?: number;
  H?: number;
  alarms?: Record<string, unknown>;
  snapshot_ids?: string[];
};

export type ObservabilitySnapshot = {
  snapshot_id: string;
  conversation_id: string;
  turn_id: string;
  run_group_id: string;
  created_at: string;
  target_thread_id: string;
  method: string;
  proxy_kind?: string | null;
  spans_considered: string[];
  influence: {
    weights?: Array<Record<string, unknown>>;
  };
  metrics: Record<string, unknown>;
  actions_taken: Record<string, unknown>;
};

export type ObservabilitySpan = {
  span_id: string;
  conversation_id: string;
  created_at: string;
  source_turn_ids: string[];
  text: string;
  token_count_est: number;
  thread_id: string;
  span_type: string;
  trust: Record<string, unknown>;
  recency: Record<string, unknown>;
  links: Record<string, unknown>;
  quarantined_until?: string | null;
};

export type ObservabilityTurn = {
  turn_id: string;
  conversation_id: string;
  created_at: string;
  speaker: string;
  text: string;
  tool_name?: string | null;
  tool_payload_ref?: string | null;
  token_count?: number | null;
  thread_hint?: string | null;
};

export type ObservabilityGovernanceLog = {
  event_id: string;
  created_at: string;
  event_type: string;
  snapshot_id?: string | null;
  details: Record<string, unknown>;
};

import type {
  CoreMemory,
  CoreSession,
  CoreStats,
  ObservabilityConversation,
  ObservabilityRunGroup,
  ObservabilitySpan,
  ObservabilityTurn,
} from "@/lib/types";

export type DataTrack = "core" | "observability";

export type CoreSessionsResponse = {
  items: CoreSession[];
  limit: number;
  offset: number;
  total: number;
};

export type CoreMemoriesResponse = {
  items: CoreMemory[];
  limit: number;
  offset: number;
  total: number;
};

export type ObservabilityThread = {
  thread_id: string;
  conversation_id: string;
  name: string;
  summary: string;
  created_at: string;
  updated_at: string;
  span_count: number;
  last_activity_at: string;
};

export type ObservabilityWorkingContext = {
  working_context_id: string;
  conversation_id: string;
  built_at: string;
  target_thread_id: string;
  selected_span_ids: string[];
  assembled_text: string;
  token_count_est: number;
  rationale: {
    selection_method?: string;
    selection_log?: Record<string, unknown>;
  };
};

export type ObservabilityMemoryEntry = {
  memory_id: string;
  conversation_id: string | null;
  created_at: string;
  updated_at: string;
  memory_type: "episodic" | "semantic" | "procedural";
  title: string;
  content: string;
  tags: string[];
  strength: number;
  status: "active" | "deprecated" | "quarantined";
  provenance: {
    source_turn_ids?: string[];
    source_span_ids?: string[];
  };
  eval: {
    success_count?: number;
    failure_count?: number;
    last_applied_at?: string | null;
  };
};

export type ObservabilityTelemetryListResponse = {
  snapshots: Array<{
    snapshot_id: string;
    conversation_id: string;
    turn_id: string;
    run_group_id: string;
    created_at: string;
    target_thread_id: string;
    method: string;
    proxy_kind?: string | null;
    spans_considered: string[];
    influence: Record<string, unknown>;
    metrics: Record<string, unknown>;
    actions_taken: Record<string, unknown>;
  }>;
};

export type ObservabilityRunGroupsResponse = {
  run_groups: ObservabilityRunGroup[];
};

export type ObservabilityRunExplain = {
  snapshot: Record<string, unknown>;
  influence_weights: Array<Record<string, unknown>>;
  alarm_explanations: Record<
    string,
    {
      triggered: boolean;
      explanation: string;
    }
  >;
  diagnostic_summary: string;
};

export interface OverviewSummaryVM {
  core: {
    totalMemories: number;
    totalSessions: number;
    tagCount: number;
  };
  observability: {
    conversationCount: number;
    recentRunCount: number;
    recentLearnedMemoryCount: number;
  };
  systemStatus: {
    tone: "healthy" | "partial" | "limited";
    sentence: string;
  };
  funnel: {
    conversationEvents: number;
    highlightsExtracted: number;
    learnedSignals?: number;
    memoryStored: number;
    notes: string[];
  };
  selectedConversation?: ConversationSummaryVM;
}

export interface ConversationSummaryVM {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messageCount?: number;
  threadCount?: number;
  latestRunAt?: string;
}

export interface MessageVM {
  id: string;
  role: "user" | "assistant" | "system" | "tool";
  text: string;
  createdAt: string;
  sequence?: number;
}

export interface ActiveContextVM {
  conversationId: string;
  assembledText: string;
  selectedHighlightIds: string[];
  selectionLog: string[];
  createdAt: string;
}

export interface RelationshipVM {
  kind: "semantic_neighbor" | "provenance" | "contradiction" | "source";
  sourceId: string;
  targetId: string;
  label: string;
  evidence?: string;
}

export interface HighlightVM {
  id: string;
  conversationId: string;
  threadId?: string;
  label: string;
  rawType: string;
  text: string;
  trust?: number;
  recency?: string;
  quarantinedUntil?: string | null;
  sourceMessageIds: string[];
  links: RelationshipVM[];
}

export interface MemoryCardVM {
  id: string;
  track: DataTrack;
  title: string;
  body: string;
  kind: string;
  status?: string;
  tags: string[];
  sourceConversationId?: string;
  sourceMessageIds?: string[];
  whyItMatters: string[];
  createdAt?: string;
  updatedAt?: string;
}

export interface RelationshipInspectorVM {
  entityId: string;
  entityType: "conversation" | "highlight" | "memory";
  title: string;
  track?: DataTrack;
  outgoing: RelationshipVM[];
  incoming: RelationshipVM[];
  contradictions: RelationshipVM[];
  references: RelationshipVM[];
}

export interface LearningModeFieldVM {
  key: "activeContextSize" | "learningDepth" | "focusStrategy" | "pinnedTopicId";
  label: string;
  helperText: string;
  editable: boolean;
  value: string | number | null;
}

export interface LearningModeVM {
  conversationId: string;
  fields: LearningModeFieldVM[];
  informationalNotes: string[];
}

export interface RunSummaryVM {
  runGroupId: string;
  conversationId: string;
  createdAtMin?: string;
  createdAtMax?: string;
  targetThreadId?: string;
  hasProxy: boolean;
  hasAblation: boolean;
  coff?: number;
  entropy?: number;
  alarms: string[];
  snapshotIds: string[];
}

export type ProductConversationBundle = {
  conversations: ObservabilityConversation[];
  turns: ObservabilityTurn[];
  threads: ObservabilityThread[];
  workingContext: ObservabilityWorkingContext | null;
  highlights: ObservabilitySpan[];
  memoryEntries: ObservabilityMemoryEntry[];
  runGroups: ObservabilityRunGroup[];
  latestSnapshots: ObservabilityTelemetryListResponse["snapshots"];
};

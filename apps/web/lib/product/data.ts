import { HttpError, requestPayload } from "@/lib/client";
import { isRecord } from "@/lib/format";
import type {
  CoreMemory,
  CoreSession,
  CoreStats,
  ObservabilityConversation,
  ObservabilityRunGroup,
  ObservabilitySpan,
  ObservabilityTurn,
} from "@/lib/types";

import type {
  ActiveContextVM,
  ConversationSummaryVM,
  CoreMemoriesResponse,
  CoreSessionsResponse,
  HighlightVM,
  LearningModeFieldVM,
  LearningModeVM,
  MemoryCardVM,
  ObservabilityMemoryEntry,
  ObservabilityRunExplain,
  ObservabilityRunGroupsResponse,
  ObservabilityTelemetryListResponse,
  ObservabilityThread,
  ObservabilityWorkingContext,
  OverviewSummaryVM,
  ProductConversationBundle,
  RelationshipInspectorVM,
  RelationshipVM,
  RunSummaryVM,
} from "./types";

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.filter((item): item is string => typeof item === "string");
}

function summarizeMemoryReason(parts: Array<string | null | undefined>): string[] {
  return parts.filter((value): value is string => Boolean(value && value.trim()));
}

export async function getCoreStats() {
  const response = await requestPayload<CoreStats>("/api/core/stats/overview");
  return response.data;
}

export async function getCoreSessions(limit = 8) {
  const response = await requestPayload<CoreSessionsResponse>(
    `/api/core/sessions?limit=${limit}`,
  );
  return response.data;
}

export async function getCoreMemories(limit = 12, sessionId?: string) {
  const search = new URLSearchParams({ limit: String(limit) });
  if (sessionId) {
    search.set("session_id", sessionId);
  }
  const response = await requestPayload<CoreMemoriesResponse>(
    `/api/core/memories?${search.toString()}`,
  );
  return response.data;
}

export async function getConversations() {
  const response = await requestPayload<ObservabilityConversation[]>(
    "/api/obs/v2/conversations",
  );
  return response.data;
}

export async function getConversationTurns(conversationId: string) {
  const response = await requestPayload<ObservabilityTurn[]>(
    `/api/obs/v2/conversations/${conversationId}/turns`,
  );
  return response.data;
}

export async function getConversationThreads(conversationId: string) {
  const response = await requestPayload<ObservabilityThread[]>(
    `/api/obs/v2/conversations/${conversationId}/threads`,
  );
  return response.data;
}

export async function getLatestWorkingContext(conversationId: string) {
  try {
    const response = await requestPayload<ObservabilityWorkingContext>(
      `/api/obs/v2/conversations/${conversationId}/working_context/latest`,
    );
    return response.data;
  } catch (error) {
    if (error instanceof HttpError && error.status === 404) {
      return null;
    }
    throw error;
  }
}

export async function getHighlights(conversationId: string) {
  const response = await requestPayload<ObservabilitySpan[]>(
    `/api/obs/v2/conversations/${conversationId}/spans?include_quarantined=true`,
  );
  return response.data;
}

export async function getObservabilityMemory(conversationId?: string) {
  const search = new URLSearchParams();
  if (conversationId) {
    search.set("conversation_id", conversationId);
  }
  const query = search.toString();
  const response = await requestPayload<ObservabilityMemoryEntry[]>(
    `/api/obs/v2/memory${query ? `?${query}` : ""}`,
  );
  return response.data;
}

export async function getRecentRunGroups(conversationId: string, limit = 10) {
  const response = await requestPayload<ObservabilityRunGroupsResponse>(
    `/api/obs/v2/conversations/${conversationId}/telemetry/run_groups/recent?limit=${limit}`,
  );
  return response.data.run_groups;
}

export async function getRunGroupDetail(conversationId: string, runGroupId: string) {
  const response = await requestPayload<ObservabilityTelemetryListResponse>(
    `/api/obs/v2/conversations/${conversationId}/telemetry/run_groups/${runGroupId}`,
  );
  return response.data.snapshots;
}

export async function getLatestTelemetry(conversationId: string) {
  const response = await requestPayload<ObservabilityTelemetryListResponse>(
    `/api/obs/v2/conversations/${conversationId}/telemetry/latest`,
  );
  return response.data.snapshots;
}

export async function getRunExplain(conversationId: string, snapshotId: string) {
  const response = await requestPayload<ObservabilityRunExplain>(
    `/api/obs/v2/conversations/${conversationId}/telemetry/snapshots/${snapshotId}/explain`,
  );
  return response.data;
}

export async function updateConversationSettings(
  conversation: ObservabilityConversation,
  values: {
    max_context_tokens: number;
    telemetry_mode: string;
    target_thread_mode: string;
    pinned_thread_id: string | null;
  },
) {
  const response = await requestPayload<ObservabilityConversation>(
    `/api/obs/v2/conversations/${conversation.conversation_id}`,
    {
      method: "PATCH",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        title: conversation.title,
        settings: values,
      }),
    },
  );
  return response.data;
}

export async function getConversationBundle(
  conversationId: string,
): Promise<ProductConversationBundle> {
  const [conversations, turns, threads, workingContext, highlights, memoryEntries, runGroups, latestSnapshots] =
    await Promise.all([
      getConversations(),
      getConversationTurns(conversationId),
      getConversationThreads(conversationId),
      getLatestWorkingContext(conversationId),
      getHighlights(conversationId),
      getObservabilityMemory(conversationId),
      getRecentRunGroups(conversationId, 8),
      getLatestTelemetry(conversationId),
    ]);

  return {
    conversations,
    turns,
    threads,
    workingContext,
    highlights,
    memoryEntries,
    runGroups,
    latestSnapshots,
  };
}

export function toConversationSummary(
  conversation: ObservabilityConversation,
  messageCount?: number,
  threadCount?: number,
  latestRunAt?: string,
): ConversationSummaryVM {
  return {
    id: conversation.conversation_id,
    title: conversation.title,
    createdAt: conversation.created_at,
    updatedAt: conversation.updated_at,
    messageCount,
    threadCount,
    latestRunAt,
  };
}

export function toMessageVM(turn: ObservabilityTurn, sequence: number) {
  return {
    id: turn.turn_id,
    role:
      turn.speaker === "tool" || turn.speaker === "assistant" || turn.speaker === "user"
        ? turn.speaker
        : "system",
    text: turn.text,
    createdAt: turn.created_at,
    sequence,
  } as const;
}

function toRelationshipListFromLinks(
  sourceId: string,
  links: ObservabilitySpan["links"],
): RelationshipVM[] {
  if (!isRecord(links)) {
    return [];
  }

  const relationships: RelationshipVM[] = [];
  const semantic = asStringArray(links.semantic_neighbors);
  const provenance = asStringArray(links.provenance);
  const contradictions = asStringArray(links.contradictions);

  semantic.forEach((targetId) => {
    relationships.push({
      kind: "semantic_neighbor",
      sourceId,
      targetId,
      label: "Related highlight",
    });
  });

  provenance.forEach((targetId) => {
    relationships.push({
      kind: "provenance",
      sourceId,
      targetId,
      label: "Built from earlier context",
    });
  });

  contradictions.forEach((targetId) => {
    relationships.push({
      kind: "contradiction",
      sourceId,
      targetId,
      label: "Potential contradiction",
    });
  });

  return relationships;
}

export function toHighlightVM(span: ObservabilitySpan): HighlightVM {
  const trust = isRecord(span.trust) ? span.trust : {};
  const recency = isRecord(span.recency) ? recencyLabel(span.recency.last_used_at) : undefined;

  return {
    id: span.span_id,
    conversationId: span.conversation_id,
    threadId: span.thread_id,
    label:
      span.span_type === "claim"
        ? "Claim highlight"
        : span.span_type === "instruction"
          ? "Instruction highlight"
          : "Conversation highlight",
    rawType: span.span_type,
    text: span.text,
    trust: typeof trust.score === "number" ? trust.score : undefined,
    recency,
    quarantinedUntil: span.quarantined_until ?? null,
    sourceMessageIds: span.source_turn_ids || [],
    links: toRelationshipListFromLinks(span.span_id, span.links),
  };
}

function recencyLabel(value: unknown) {
  if (typeof value !== "string" || !value) {
    return undefined;
  }
  return `Used ${new Date(value).toLocaleDateString()}`;
}

export function toCoreMemoryCard(memory: CoreMemory): MemoryCardVM {
  return {
    id: memory.id,
    track: "core",
    title: memory.name || "Saved memory",
    body: memory.content,
    kind: "Saved memory",
    tags: memory.tags,
    sourceConversationId: undefined,
    sourceMessageIds: [],
    createdAt: memory.created_at ?? undefined,
    updatedAt: memory.updated_at ?? undefined,
    whyItMatters: summarizeMemoryReason([
      memory.session_id ? `Available to session ${memory.session_id}.` : null,
      memory.tags.length ? `Tagged for ${memory.tags.join(", ")}.` : null,
    ]),
  };
}

export function toObservabilityMemoryCard(memory: ObservabilityMemoryEntry): MemoryCardVM {
  return {
    id: memory.memory_id,
    track: "observability",
    title: memory.title,
    body: memory.content,
    kind: `${memory.memory_type} memory`,
    status: memory.status,
    tags: memory.tags,
    sourceConversationId: memory.conversation_id ?? undefined,
    sourceMessageIds: memory.provenance?.source_turn_ids ?? [],
    createdAt: memory.created_at,
    updatedAt: memory.updated_at,
    whyItMatters: summarizeMemoryReason([
      memory.provenance?.source_span_ids?.length
        ? `Built from ${memory.provenance.source_span_ids.length} highlight(s).`
        : null,
      typeof memory.eval?.success_count === "number"
        ? `Helped successfully ${memory.eval.success_count} time(s).`
        : null,
      typeof memory.eval?.failure_count === "number" && memory.eval.failure_count > 0
        ? `Has ${memory.eval.failure_count} recorded failures.`
        : null,
    ]),
  };
}

export function toRunSummaryVM(
  conversationId: string,
  runGroup: ObservabilityRunGroup,
): RunSummaryVM {
  const alarms = isRecord(runGroup.alarms)
    ? Object.entries(runGroup.alarms)
        .filter(([, value]) => Boolean(value))
        .map(([key]) => key)
    : [];

  return {
    runGroupId: runGroup.run_group_id,
    conversationId,
    createdAtMin: runGroup.created_at_min,
    createdAtMax: runGroup.created_at_max,
    targetThreadId: runGroup.target_thread_id,
    hasProxy: Boolean(runGroup.has_proxy),
    hasAblation: Boolean(runGroup.has_ablation),
    coff: typeof runGroup.Coff === "number" ? runGroup.Coff : undefined,
    entropy: typeof runGroup.H === "number" ? runGroup.H : undefined,
    alarms,
    snapshotIds: Array.isArray(runGroup.snapshot_ids) ? runGroup.snapshot_ids : [],
  };
}

export function buildOverviewSummary(input: {
  coreStats: CoreStats;
  coreSessions: CoreSession[];
  coreMemories: CoreMemory[];
  conversations: ObservabilityConversation[];
  turns: ObservabilityTurn[];
  highlights: ObservabilitySpan[];
  observedMemories: ObservabilityMemoryEntry[];
  runGroups: ObservabilityRunGroup[];
}): OverviewSummaryVM {
  const conversationCount = input.conversations.length;
  const recentRunCount = input.runGroups.length;
  const learnedSignals = input.observedMemories.length;
  const memoryStored = input.coreStats.total_memories + input.observedMemories.length;
  const status = deriveSystemStatus({
    conversationCount,
    highlightCount: input.highlights.length,
    durableCount: input.coreStats.total_memories,
    learnedCount: input.observedMemories.length,
    runCount: recentRunCount,
  });

  return {
    core: {
      totalMemories: input.coreStats.total_memories,
      totalSessions: input.coreStats.total_sessions,
      tagCount: input.coreStats.top_tags.length,
    },
    observability: {
      conversationCount,
      recentRunCount,
      recentLearnedMemoryCount: input.observedMemories.length,
    },
    systemStatus: status,
    funnel: {
      conversationEvents: input.turns.length,
      highlightsExtracted: input.highlights.length,
      learnedSignals,
      memoryStored,
      notes: [
        "Learned Signals is estimated from current Observability memory data, not a first-class promotion API.",
        "Memory stored includes records currently visible across Core and Observability.",
      ],
    },
    selectedConversation: input.conversations[0]
      ? toConversationSummary(
          input.conversations[0],
          input.turns.length,
          undefined,
          input.runGroups[0]?.created_at_max,
        )
      : undefined,
  };
}

function deriveSystemStatus(input: {
  conversationCount: number;
  highlightCount: number;
  durableCount: number;
  learnedCount: number;
  runCount: number;
}): OverviewSummaryVM["systemStatus"] {
  if (!input.conversationCount) {
    return {
      tone: "limited",
      sentence: "StateLock is ready, but it does not have conversation data to learn from yet.",
    };
  }

  if (input.highlightCount > 0 && input.durableCount > 0) {
    return {
      tone: "healthy",
      sentence: "StateLock is actively tracking conversations and carrying forward signals into stored memory.",
    };
  }

  if (input.highlightCount > 0 && input.durableCount === 0) {
    return {
      tone: "partial",
      sentence: "StateLock is capturing highlights, but durable memory is currently limited.",
    };
  }

  if (input.runCount > 0 || input.learnedCount > 0) {
    return {
      tone: "partial",
      sentence: "StateLock is operating with partial Observability data while memory formation remains conservative.",
    };
  }

  return {
    tone: "partial",
    sentence: "StateLock is actively tracking conversations and waiting for stronger signals before keeping more memory.",
  };
}

export function toActiveContextVM(
  workingContext: ProductConversationBundle["workingContext"],
): ActiveContextVM | null {
  if (!workingContext) {
    return null;
  }

  const selectionLog = isRecord(workingContext.rationale?.selection_log)
    ? Object.entries(workingContext.rationale.selection_log).map(
        ([key, value]) => `${key}: ${String(value)}`,
      )
    : [];

  return {
    conversationId: workingContext.conversation_id,
    assembledText: sanitizeActiveContextText(workingContext.assembled_text),
    selectedHighlightIds: workingContext.selected_span_ids,
    selectionLog,
    createdAt: workingContext.built_at,
  };
}

function sanitizeActiveContextText(text: string) {
  return text.replace(/\s*\[span:[^\]]+\]/g, "");
}

export function buildRelationshipInspector(input: {
  entityType: "conversation" | "highlight" | "memory";
  entityId: string;
  conversations: ObservabilityConversation[];
  highlights: HighlightVM[];
  memories: MemoryCardVM[];
}): RelationshipInspectorVM | null {
  if (input.entityType === "conversation") {
    const conversation = input.conversations.find(
      (item) => item.conversation_id === input.entityId,
    );
    if (!conversation) {
      return null;
    }

    const relatedHighlights = input.highlights
      .filter((highlight) => highlight.conversationId === input.entityId)
      .slice(0, 12)
      .map((highlight) => ({
        kind: "source" as const,
        sourceId: input.entityId,
        targetId: highlight.id,
        label: "Contains highlight",
      }));
    const relatedMemories = input.memories
      .filter((memory) => memory.sourceConversationId === input.entityId)
      .slice(0, 12)
      .map((memory) => ({
        kind: "source" as const,
        sourceId: input.entityId,
        targetId: memory.id,
        label: "Produced memory",
      }));

    return {
      entityId: input.entityId,
      entityType: "conversation",
      title: conversation.title,
      outgoing: [...relatedHighlights, ...relatedMemories],
      incoming: [],
      contradictions: [],
      references: [],
    };
  }

  if (input.entityType === "highlight") {
    const highlight = input.highlights.find((item) => item.id === input.entityId);
    if (!highlight) {
      return null;
    }

    const contradictions = highlight.links.filter((item) => item.kind === "contradiction");
    const references = highlight.sourceMessageIds.map((messageId) => ({
      kind: "source" as const,
      sourceId: highlight.id,
      targetId: messageId,
      label: "Draws from message",
    }));

    return {
      entityId: highlight.id,
      entityType: "highlight",
      title: highlight.label,
      outgoing: highlight.links.filter((item) => item.kind !== "contradiction"),
      incoming: [],
      contradictions,
      references,
    };
  }

  const memory = input.memories.find((item) => item.id === input.entityId);
  if (!memory) {
    return null;
  }

  const references: RelationshipVM[] = [];
  if (memory.sourceConversationId) {
    references.push({
      kind: "source",
      sourceId: memory.id,
      targetId: memory.sourceConversationId,
      label: "Learned from conversation",
    });
  }
  memory.sourceMessageIds?.forEach((messageId) => {
    references.push({
      kind: "source",
      sourceId: memory.id,
      targetId: messageId,
      label: "Linked source message",
    });
  });

  return {
    entityId: memory.id,
    entityType: "memory",
    title: memory.title,
    track: memory.track,
    outgoing: [],
    incoming: [],
    contradictions: [],
    references,
  };
}

export function toLearningModeVM(
  conversation: ObservabilityConversation,
): LearningModeVM {
  const settings = conversation.settings;
  const fields: LearningModeFieldVM[] = [
    {
      key: "activeContextSize",
      label: "Active Context Size",
      helperText:
        "How much recent and relevant information StateLock tries to keep in play.",
      editable: true,
      value: settings.max_context_tokens,
    },
    {
      key: "learningDepth",
      label: "Learning Depth",
      helperText:
        "How closely StateLock watches each conversation for patterns worth keeping.",
      editable: true,
      value: settings.telemetry_mode,
    },
    {
      key: "focusStrategy",
      label: "Focus Strategy",
      helperText:
        "How StateLock decides which topic or thread deserves attention.",
      editable: true,
      value: settings.target_thread_mode,
    },
    {
      key: "pinnedTopicId",
      label: "Pinned Topic",
      helperText:
        "A topic you want StateLock to keep centered even as the conversation shifts.",
      editable: true,
      value: settings.pinned_thread_id ?? "",
    },
  ];

  return {
    conversationId: conversation.conversation_id,
    fields,
    informationalNotes: [
      "Learning Mode currently reflects stable conversation settings already implemented in Observability.",
      "Richer policy profiles remain an architecture direction, not a first-class runtime feature.",
    ],
  };
}

"use client";

import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { TrackSourceBadge } from "@/components/track-source-badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  buildRelationshipInspector,
  getConversations,
  getCoreMemories,
  getHighlights,
  getObservabilityMemory,
  toCoreMemoryCard,
  toHighlightVM,
  toObservabilityMemoryCard,
} from "@/lib/product/data";

import {
  ProductEmptyState,
  ProductErrorState,
  ProductLoadingState,
  ProductPageHeader,
} from "./primitives";

type EntityKind = "memory" | "highlight" | "conversation";

export function RelationshipsPage({
  initialKind,
  initialId,
  initialConversationId,
}: {
  initialKind?: EntityKind;
  initialId?: string;
  initialConversationId?: string;
}) {
  const preloadedKind = initialKind ?? null;
  const preloadedId = initialId ?? null;
  const preloadedConversationId = initialConversationId ?? null;

  const conversationsQuery = useQuery({
    queryKey: ["product", "conversations"],
    queryFn: getConversations,
  });
  const coreMemoriesQuery = useQuery({
    queryKey: ["product", "relationships", "core-memory"],
    queryFn: () => getCoreMemories(12),
  });
  const observedMemoriesQuery = useQuery({
    queryKey: ["product", "relationships", "observability-memory"],
    queryFn: () => getObservabilityMemory(),
  });

  const [highlightConversationId, setHighlightConversationId] = useState(
    preloadedConversationId || "",
  );
  const [selectedKind, setSelectedKind] = useState<EntityKind>("memory");
  const [selectedId, setSelectedId] = useState("");

  useEffect(() => {
    if (!highlightConversationId && conversationsQuery.data?.[0]) {
      setHighlightConversationId(conversationsQuery.data[0].conversation_id);
    }
  }, [conversationsQuery.data, highlightConversationId]);

  const highlightsQuery = useQuery({
    queryKey: ["product", "relationships", "highlights", highlightConversationId],
    queryFn: () => getHighlights(highlightConversationId),
    enabled: Boolean(highlightConversationId),
  });

  const memories = [
    ...(observedMemoriesQuery.data ?? []).map(toObservabilityMemoryCard),
    ...(coreMemoriesQuery.data?.items ?? []).map(toCoreMemoryCard),
  ].filter((memory) => !isPlaceholderMemory(memory));
  const highlights = (highlightsQuery.data ?? []).map(toHighlightVM);
  const conversations = conversationsQuery.data ?? [];
  const pendingDefaultSources =
    conversationsQuery.isLoading ||
    coreMemoriesQuery.isLoading ||
    observedMemoriesQuery.isLoading ||
    (Boolean(highlightConversationId) && highlightsQuery.isLoading);
  const firstMemory = memories[0];
  const firstHighlight = highlights[0];
  const firstConversation = conversations[0];

  useEffect(() => {
    if (preloadedKind && preloadedId) {
      setSelectedKind(preloadedKind);
      setSelectedId(preloadedId);
      return;
    }

    if (selectedId || pendingDefaultSources) {
      return;
    }

    if (firstMemory) {
      setSelectedKind("memory");
      setSelectedId(firstMemory.id);
      if (firstMemory.sourceConversationId) {
        setHighlightConversationId(firstMemory.sourceConversationId);
      }
      return;
    }

    if (firstHighlight) {
      setSelectedKind("highlight");
      setSelectedId(firstHighlight.id);
      return;
    }

    if (firstConversation) {
      setSelectedKind("conversation");
      setSelectedId(firstConversation.conversation_id);
    }
  }, [
    firstConversation,
    firstHighlight,
    firstMemory,
    pendingDefaultSources,
    preloadedId,
    preloadedKind,
    selectedId,
  ]);

  if (
    conversationsQuery.isLoading ||
    coreMemoriesQuery.isLoading ||
    observedMemoriesQuery.isLoading
  ) {
    return <ProductLoadingState label="Loading relationships" />;
  }

  const error =
    conversationsQuery.error ||
    coreMemoriesQuery.error ||
    observedMemoriesQuery.error ||
    highlightsQuery.error;
  if (error instanceof Error) {
    return <ProductErrorState message={error.message} />;
  }

  const inspector = buildRelationshipInspector({
    entityType: selectedKind,
    entityId: selectedId,
    conversations,
    highlights,
    memories,
  });

  return (
    <div className="space-y-6 pb-8">
      <ProductPageHeader
        eyebrow="Relationships"
        title="Inspect how a signal connects"
        copy="Relationships stay inspector-first. Pick a memory, highlight, or conversation and StateLock shows the currently visible links, provenance, contradictions, and references without pretending a full graph API already exists."
      />

      <div className="grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
        <Card>
          <CardHeader>
            <CardTitle>Pick an entity</CardTitle>
            <CardDescription>
              Defaults favor recent memories, then recent highlights, then recent conversations.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3">
              <label className="text-sm text-black/60" htmlFor="relationship-kind">
                Entity type
              </label>
              <select
                className="rounded-2xl border border-black/10 bg-white/80 px-4 py-3 text-sm"
                id="relationship-kind"
                onChange={(event) => {
                  const nextKind = event.target.value as EntityKind;
                  setSelectedKind(nextKind);
                  const fallbackId =
                    nextKind === "memory"
                      ? memories[0]?.id
                      : nextKind === "highlight"
                        ? highlights[0]?.id
                        : conversations[0]?.conversation_id;
                  setSelectedId(fallbackId ?? "");
                }}
                value={selectedKind}
              >
                <option value="memory">Memory</option>
                <option value="highlight">Highlight</option>
                <option value="conversation">Conversation</option>
              </select>
            </div>
            <div className="grid gap-3">
              <label className="text-sm text-black/60" htmlFor="relationship-entity">
                Entity
              </label>
              <select
                className="rounded-2xl border border-black/10 bg-white/80 px-4 py-3 text-sm"
                id="relationship-entity"
                onChange={(event) => setSelectedId(event.target.value)}
                value={selectedId}
              >
                {selectedKind === "memory"
                  ? memories.map((memory) => (
                      <option key={memory.id} value={memory.id}>
                        {memory.title}
                      </option>
                    ))
                  : selectedKind === "highlight"
                    ? highlights.map((highlight) => (
                        <option key={highlight.id} value={highlight.id}>
                          {highlight.label}
                        </option>
                      ))
                    : conversations.map((conversation) => (
                        <option key={conversation.conversation_id} value={conversation.conversation_id}>
                          {conversation.title}
                        </option>
                      ))}
              </select>
            </div>
            {!memories.length && !highlights.length && !conversations.length ? (
              <ProductEmptyState
                title="No relationship sources yet"
                copy="StateLock needs at least one visible memory, highlight, or conversation before this inspector can preload a useful starting point."
              />
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between gap-3">
              <div>
                <CardTitle>{inspector?.title ?? "Relationship inspector"}</CardTitle>
                <CardDescription>
                  Current links exposed by the repo today.
                </CardDescription>
              </div>
              {inspector?.track ? <TrackSourceBadge track={inspector.track} /> : null}
            </div>
          </CardHeader>
          <CardContent className="space-y-5">
            {inspector ? (
              <>
                <RelationshipSection
                  title="Visible links"
                  items={inspector.outgoing}
                  empty="No direct outgoing links are visible for this entity."
                />
                <RelationshipSection
                  title="References"
                  items={inspector.references}
                  empty="No explicit references are exposed for this entity."
                />
                <RelationshipSection
                  title="Contradictions"
                  items={inspector.contradictions}
                  empty="No contradictions are currently recorded."
                />
              </>
            ) : (
              <ProductEmptyState
                title="Pick an entity to inspect"
                copy="The inspector will show current provenance, source references, and contradictions when they exist."
              />
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function isPlaceholderMemory(memory: { title: string; body: string }) {
  const text = `${memory.title} ${memory.body}`.trim().toLowerCase();
  return text === "string string" || text === "saved memory string";
}

function RelationshipSection({
  title,
  items,
  empty,
}: {
  title: string;
  items: Array<{ label: string; targetId: string }>;
  empty: string;
}) {
  return (
    <div className="rounded-3xl border border-black/10 bg-white/80 p-4">
      <p className="text-sm uppercase tracking-[0.14em] text-black/50">{title}</p>
      <div className="mt-3 space-y-2 text-sm text-black/65">
        {items.length ? (
          items.map((item) => (
            <p key={`${item.label}-${item.targetId}`}>
              {item.label}: {item.targetId}
            </p>
          ))
        ) : (
          <p>{empty}</p>
        )}
      </div>
    </div>
  );
}

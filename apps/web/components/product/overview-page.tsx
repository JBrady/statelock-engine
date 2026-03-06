"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useEffect, useState } from "react";

import { TechnicalDetailsDrawer } from "@/components/technical-details-drawer";
import { TrackSourceBadge } from "@/components/track-source-badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  buildOverviewSummary,
  getConversations,
  getCoreMemories,
  getCoreSessions,
  getCoreStats,
  getHighlights,
  getObservabilityMemory,
  getRecentRunGroups,
  getConversationTurns,
  toCoreMemoryCard,
  toObservabilityMemoryCard,
} from "@/lib/product/data";
import { formatDateTime } from "@/lib/format";

import {
  ProductEmptyState,
  ProductErrorState,
  ProductLoadingState,
  ProductMetric,
  ProductPageHeader,
} from "./primitives";

export function OverviewPage() {
  const conversationsQuery = useQuery({
    queryKey: ["product", "conversations"],
    queryFn: getConversations,
  });
  const coreStatsQuery = useQuery({
    queryKey: ["product", "core-stats"],
    queryFn: getCoreStats,
  });
  const coreSessionsQuery = useQuery({
    queryKey: ["product", "core-sessions"],
    queryFn: () => getCoreSessions(6),
  });
  const coreMemoriesQuery = useQuery({
    queryKey: ["product", "core-memories"],
    queryFn: () => getCoreMemories(6),
  });

  const [selectedConversationId, setSelectedConversationId] = useState("");

  useEffect(() => {
    if (!selectedConversationId && conversationsQuery.data?.[0]) {
      setSelectedConversationId(conversationsQuery.data[0].conversation_id);
    }
  }, [conversationsQuery.data, selectedConversationId]);

  const turnsQuery = useQuery({
    queryKey: ["product", "overview-turns", selectedConversationId],
    queryFn: () => getConversationTurns(selectedConversationId),
    enabled: Boolean(selectedConversationId),
  });
  const highlightsQuery = useQuery({
    queryKey: ["product", "overview-highlights", selectedConversationId],
    queryFn: () => getHighlights(selectedConversationId),
    enabled: Boolean(selectedConversationId),
  });
  const obsMemoryQuery = useQuery({
    queryKey: ["product", "overview-memory", selectedConversationId],
    queryFn: () => getObservabilityMemory(selectedConversationId),
    enabled: Boolean(selectedConversationId),
  });
  const runsQuery = useQuery({
    queryKey: ["product", "overview-runs", selectedConversationId],
    queryFn: () => getRecentRunGroups(selectedConversationId, 6),
    enabled: Boolean(selectedConversationId),
  });

  const loading =
    conversationsQuery.isLoading ||
    coreStatsQuery.isLoading ||
    coreSessionsQuery.isLoading ||
    coreMemoriesQuery.isLoading;
  const error =
    conversationsQuery.error ||
    coreStatsQuery.error ||
    coreSessionsQuery.error ||
    coreMemoriesQuery.error ||
    turnsQuery.error ||
    highlightsQuery.error ||
    obsMemoryQuery.error ||
    runsQuery.error;

  if (loading) {
    return <ProductLoadingState label="Loading the continuity overview" />;
  }

  if (error instanceof Error) {
    return <ProductErrorState message={error.message} />;
  }

  const conversations = conversationsQuery.data ?? [];
  const coreStats = coreStatsQuery.data;
  const coreSessions = coreSessionsQuery.data?.items ?? [];
  const coreMemories = coreMemoriesQuery.data?.items ?? [];
  const turns = turnsQuery.data ?? [];
  const highlights = highlightsQuery.data ?? [];
  const observedMemories = obsMemoryQuery.data ?? [];
  const runGroups = runsQuery.data ?? [];

  if (!coreStats) {
    return <ProductErrorState message="Core stats did not load." />;
  }

  const summary = buildOverviewSummary({
    coreStats,
    coreSessions,
    coreMemories,
    conversations,
    turns,
    highlights,
    observedMemories,
    runGroups,
  });

  const funnelData = [
    { label: "Conversation events", value: summary.funnel.conversationEvents },
    { label: "Highlights extracted", value: summary.funnel.highlightsExtracted },
    { label: "Learned Signals", value: summary.funnel.learnedSignals ?? 0 },
    { label: "Memory stored", value: summary.funnel.memoryStored },
  ];

  const observedMemoryCards = observedMemories
    .map(toObservabilityMemoryCard)
    .filter((memory) => !isPlaceholderMemory(memory));
  const coreMemoryCards = coreMemories
    .map(toCoreMemoryCard)
    .filter((memory) => !isPlaceholderMemory(memory));
  const recentExample = observedMemoryCards[0] ?? coreMemoryCards[0] ?? null;
  const recentMemoryCards = [...observedMemoryCards.slice(0, 2), ...coreMemoryCards.slice(0, 2)];

  return (
    <div className="space-y-6 pb-8">
      <ProductPageHeader
        eyebrow="Overview"
        title="A clear view of how StateLock learns"
        copy="StateLock keeps the line visible between conversations, highlights, learned signals, and stored memory. This overview stays grounded in the data the repo actually exposes today."
        actions={
          conversations.length ? (
            <div className="flex items-center gap-3">
              <label className="text-sm text-black/60" htmlFor="overview-conversation">
                Conversation
              </label>
              <select
                className="rounded-full border border-black/10 bg-white/80 px-4 py-2 text-sm"
                id="overview-conversation"
                onChange={(event) => setSelectedConversationId(event.target.value)}
                value={selectedConversationId}
              >
                {conversations.map((conversation) => (
                  <option
                    key={conversation.conversation_id}
                    value={conversation.conversation_id}
                  >
                    {conversation.title}
                  </option>
                ))}
              </select>
            </div>
          ) : null
        }
      />

      <Card className="bg-[#163038] text-white">
        <CardContent className="p-6">
          <p className="text-sm uppercase tracking-[0.18em] text-white/60">System status</p>
          <p className="mt-3 font-display text-3xl leading-tight">
            {summary.systemStatus.sentence}
          </p>
          <div className="mt-4 flex flex-wrap gap-3 text-sm text-white/72">
            <span>{summary.observability.conversationCount} conversation(s)</span>
            <span>{summary.funnel.highlightsExtracted} highlight(s)</span>
            <span>{summary.core.totalMemories} Core memories</span>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <ProductMetric label="Core memories" value={summary.core.totalMemories} />
        <ProductMetric label="Tracked sessions" value={summary.core.totalSessions} />
        <ProductMetric label="Conversations" value={summary.observability.conversationCount} />
        <ProductMetric label="Recent runs" value={summary.observability.recentRunCount} />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]">
        <Card>
          <CardHeader>
            <CardTitle>Continuity funnel</CardTitle>
            <CardDescription>
              Learned Signals is estimated from current Observability memory data,
              not a first-class promotion API.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-72">
              <div className="grid h-full content-start gap-4 pt-2">
                {funnelData.map((entry, index) => {
                  const maxValue = Math.max(...funnelData.map((item) => item.value || 1), 1);
                  const width = Math.max(24, Math.round((entry.value / maxValue) * 100));
                  const colors = [
                    "bg-[#163038]",
                    "bg-[#0e766e]",
                    "bg-[#d4a373]",
                    "bg-[#b8871d]",
                  ];

                  return (
                    <div key={entry.label} className="grid gap-2">
                      <div className="flex items-center justify-between gap-3 text-sm text-black/60">
                        <span>{entry.label}</span>
                        <span>{entry.value}</span>
                      </div>
                      <div className="h-11 rounded-full bg-black/5 p-1">
                        <div
                          className={`${colors[index]} flex h-full items-center rounded-full px-4 text-sm font-medium text-white transition-all`}
                          style={{ width: `${width}%` }}
                        >
                          {index + 1}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
            <div className="mt-4 space-y-2 text-sm text-black/60">
              {summary.funnel.notes.map((note) => (
                <p key={note}>{note}</p>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Why This Matters</CardTitle>
            <CardDescription>
              A compact example of the value signal StateLock is surfacing right now.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {recentExample ? (
              <>
                <div className="flex items-center justify-between gap-3">
                  <h3 className="font-display text-xl text-ink">{recentExample.title}</h3>
                  <TrackSourceBadge track={recentExample.track} />
                </div>
                <p className="text-sm leading-6 text-black/70">{recentExample.body}</p>
                <div className="space-y-2 text-sm text-black/60">
                  {recentExample.whyItMatters.length ? (
                    recentExample.whyItMatters.map((reason) => <p key={reason}>{reason}</p>)
                  ) : (
                    <p>StateLock has stored this signal, but the repo does not expose a richer reason trail yet.</p>
                  )}
                </div>
              </>
            ) : (
              <ProductEmptyState
                title="No saved example yet"
                copy="Once Core or Observability memory records exist, this card will show a recent example and its visible rationale."
              />
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Recent conversations</CardTitle>
            <CardDescription>Observable conversations currently available.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {conversations.length ? (
              conversations.slice(0, 4).map((conversation) => (
                <div key={conversation.conversation_id} className="rounded-3xl border border-black/10 bg-white/80 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <h3 className="font-display text-lg">{conversation.title}</h3>
                    <Link
                      className="text-sm text-teal"
                      href={`/conversations?conversationId=${conversation.conversation_id}`}
                    >
                      Open
                    </Link>
                  </div>
                  <p className="mt-2 text-sm text-black/60">
                    Updated {formatDateTime(conversation.updated_at)}
                  </p>
                </div>
              ))
            ) : (
              <ProductEmptyState
                title="No conversations yet"
                copy="Run the Observability seed flow to see conversation timelines here."
              />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent runs</CardTitle>
            <CardDescription>Current run groups for the selected conversation.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {runGroups.length ? (
              runGroups.slice(0, 4).map((runGroup) => (
                <div key={runGroup.run_group_id} className="rounded-3xl border border-black/10 bg-white/80 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <h3 className="font-display text-lg">{runGroup.run_group_id.slice(0, 8)}</h3>
                    <Link
                      className="text-sm text-teal"
                      href={`/runs?conversationId=${selectedConversationId}&runGroupId=${runGroup.run_group_id}`}
                    >
                      Inspect
                    </Link>
                  </div>
                  <p className="mt-2 text-sm text-black/60">
                    {formatDateTime(runGroup.created_at_max)}
                  </p>
                </div>
              ))
            ) : (
              <ProductEmptyState
                title="No recent runs"
                copy="Telemetry run groups appear here once Observability has processed a conversation."
              />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent memory</CardTitle>
            <CardDescription>State visible across both tracks.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {recentMemoryCards.length ? (
              recentMemoryCards.map((memory) => (
                <div key={`${memory.track}-${memory.id}`} className="rounded-3xl border border-black/10 bg-white/80 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <h3 className="font-display text-lg">{memory.title}</h3>
                    <TrackSourceBadge track={memory.track} />
                  </div>
                  <p className="mt-2 text-sm text-black/70">{memory.body}</p>
                </div>
              ))
            ) : (
              <ProductEmptyState
                title="No memory records yet"
                copy="Create Core memories or run Observability distillation to populate this panel."
              />
            )}
          </CardContent>
        </Card>
      </div>

      <div className="flex justify-end">
        <TechnicalDetailsDrawer title="Overview technical details">
          <pre className="text-xs leading-6 text-black/75">
            {JSON.stringify(
              {
                summary,
                coreSessions,
                selectedConversationId,
                turns,
                highlights,
                observedMemories,
                runGroups,
              },
              null,
              2,
            )}
          </pre>
        </TechnicalDetailsDrawer>
      </div>
    </div>
  );
}

function isPlaceholderMemory(memory: { title: string; body: string }) {
  const text = `${memory.title} ${memory.body}`.trim().toLowerCase();
  return text === "string string" || text === "saved memory string";
}

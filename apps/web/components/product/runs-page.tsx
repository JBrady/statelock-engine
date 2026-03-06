"use client";

import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { TechnicalDetailsDrawer } from "@/components/technical-details-drawer";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  getConversations,
  getLatestTelemetry,
  getRecentRunGroups,
  getRunExplain,
  getRunGroupDetail,
  toRunSummaryVM,
} from "@/lib/product/data";
import { formatDateTime, formatNumber } from "@/lib/format";

import {
  ProductEmptyState,
  ProductErrorState,
  ProductLoadingState,
  ProductPageHeader,
} from "./primitives";

export function RunsPage({
  initialConversationId = "",
  initialRunGroupId = "",
}: {
  initialConversationId?: string;
  initialRunGroupId?: string;
}) {
  const conversationsQuery = useQuery({
    queryKey: ["product", "conversations"],
    queryFn: getConversations,
  });
  const [selectedConversationId, setSelectedConversationId] = useState(
    initialConversationId,
  );
  const [selectedRunGroupId, setSelectedRunGroupId] = useState(initialRunGroupId);

  useEffect(() => {
    if (!selectedConversationId && conversationsQuery.data?.[0]) {
      setSelectedConversationId(conversationsQuery.data[0].conversation_id);
    }
  }, [conversationsQuery.data, selectedConversationId]);

  const runGroupsQuery = useQuery({
    queryKey: ["product", "runs", selectedConversationId],
    queryFn: () => getRecentRunGroups(selectedConversationId, 10),
    enabled: Boolean(selectedConversationId),
  });
  const latestQuery = useQuery({
    queryKey: ["product", "runs", "latest", selectedConversationId],
    queryFn: () => getLatestTelemetry(selectedConversationId),
    enabled: Boolean(selectedConversationId),
  });

  useEffect(() => {
    if (!selectedRunGroupId && runGroupsQuery.data?.[0]) {
      setSelectedRunGroupId(runGroupsQuery.data[0].run_group_id);
    }
  }, [runGroupsQuery.data, selectedRunGroupId]);

  const detailQuery = useQuery({
    queryKey: ["product", "runs", "detail", selectedConversationId, selectedRunGroupId],
    queryFn: () => getRunGroupDetail(selectedConversationId, selectedRunGroupId),
    enabled: Boolean(selectedConversationId && selectedRunGroupId),
  });
  const explainQuery = useQuery({
    queryKey: [
      "product",
      "runs",
      "explain",
      selectedConversationId,
      detailQuery.data?.[0]?.snapshot_id,
    ],
    queryFn: () => getRunExplain(selectedConversationId, detailQuery.data?.[0]?.snapshot_id ?? ""),
    enabled: Boolean(selectedConversationId && detailQuery.data?.[0]?.snapshot_id),
  });

  if (conversationsQuery.isLoading) {
    return <ProductLoadingState label="Loading runs" />;
  }

  const error =
    conversationsQuery.error ||
    runGroupsQuery.error ||
    latestQuery.error ||
    detailQuery.error ||
    explainQuery.error;
  if (error instanceof Error) {
    return <ProductErrorState message={error.message} />;
  }

  const conversations = conversationsQuery.data ?? [];
  const runGroups = (runGroupsQuery.data ?? []).map((runGroup) =>
    toRunSummaryVM(selectedConversationId, runGroup),
  );
  const selectedRun = runGroups.find((runGroup) => runGroup.runGroupId === selectedRunGroupId);

  return (
    <div className="space-y-6 pb-8">
      <ProductPageHeader
        eyebrow="Runs"
        title="Inspect how StateLock evaluated the conversation"
        copy="Runs stay conversation-scoped because the current backend does not expose a global run index. The UI makes that limitation explicit instead of faking one."
        actions={
          conversations.length ? (
            <select
              className="rounded-full border border-black/10 bg-white/80 px-4 py-2 text-sm"
              onChange={(event) => {
                setSelectedConversationId(event.target.value);
                setSelectedRunGroupId("");
              }}
              value={selectedConversationId}
            >
              {conversations.map((conversation) => (
                <option key={conversation.conversation_id} value={conversation.conversation_id}>
                  {conversation.title}
                </option>
              ))}
            </select>
          ) : null
        }
      />

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Recent run groups</CardTitle>
            <CardDescription>Recent run activity for the selected conversation.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {runGroups.length ? (
              runGroups.map((run) => (
                <button
                  className={`w-full rounded-3xl border p-4 text-left transition ${
                    run.runGroupId === selectedRunGroupId
                      ? "border-moss bg-moss/10"
                      : "border-black/10 bg-white/80"
                  }`}
                  key={run.runGroupId}
                  onClick={() => setSelectedRunGroupId(run.runGroupId)}
                  type="button"
                >
                  <h3 className="font-display text-lg text-ink">{run.runGroupId.slice(0, 8)}</h3>
                  <p className="mt-2 text-sm text-black/60">
                    {formatDateTime(run.createdAtMax)} · alarms {run.alarms.length}
                  </p>
                </button>
              ))
            ) : (
              <ProductEmptyState
                title="No run groups yet"
                copy="Telemetry activity for this conversation has not produced visible run groups."
              />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{selectedRun ? "Run detail" : "Select a run group"}</CardTitle>
            <CardDescription>
              Summary values come from the existing recent run-group payload.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            {selectedRun ? (
              <>
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="rounded-3xl border border-black/10 bg-white/80 p-4">
                    <p className="text-sm uppercase tracking-[0.14em] text-black/50">Coverage</p>
                    <div className="mt-3 space-y-2 text-sm text-black/65">
                      <p>Proxy: {String(selectedRun.hasProxy)}</p>
                      <p>Ablation: {String(selectedRun.hasAblation)}</p>
                      <p>Target topic: {selectedRun.targetThreadId || "Not specified"}</p>
                    </div>
                  </div>
                  <div className="rounded-3xl border border-black/10 bg-white/80 p-4">
                    <p className="text-sm uppercase tracking-[0.14em] text-black/50">Metrics</p>
                    <div className="mt-3 space-y-2 text-sm text-black/65">
                      <p>Off-thread coupling: {formatNumber(selectedRun.coff)}</p>
                      <p>Influence entropy: {formatNumber(selectedRun.entropy)}</p>
                      <p>Alarms: {selectedRun.alarms.length ? selectedRun.alarms.join(", ") : "none"}</p>
                    </div>
                  </div>
                </div>

                <div className="rounded-3xl border border-black/10 bg-white/80 p-4">
                  <p className="text-sm uppercase tracking-[0.14em] text-black/50">Explain summary</p>
                  <p className="mt-3 text-sm leading-7 text-black/70">
                    {explainQuery.data?.diagnostic_summary ??
                      "Detailed explain output is not available for this run yet."}
                  </p>
                </div>
              </>
            ) : (
              <ProductEmptyState
                title="Pick a run group"
                copy="Select a run group to inspect coverage, metrics, and the latest explain summary."
              />
            )}
          </CardContent>
        </Card>
      </div>

      <div className="flex justify-end">
        <TechnicalDetailsDrawer title="Run technical details">
          <pre className="text-xs leading-6 text-black/75">
            {JSON.stringify(
              {
                latestSnapshots: latestQuery.data,
                runDetails: detailQuery.data,
                explain: explainQuery.data,
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

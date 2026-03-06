"use client";

import { useEffect, useState } from "react";

import { JsonBlock } from "@/components/json-block";
import { LoadState } from "@/components/load-state";
import { PageHeader } from "@/components/page-header";
import { requestPayload } from "@/lib/client";
import { isRecord, scalarEntries } from "@/lib/format";
import type {
  CoreStats,
  ObservabilityConversation,
  ObservabilityRunGroup,
  ObservabilitySnapshot,
} from "@/lib/types";

type RunGroupsResponse = { run_groups: ObservabilityRunGroup[] };
type LatestResponse = { snapshots: ObservabilitySnapshot[] };

export default function MetricsPage() {
  const [coreStats, setCoreStats] = useState<CoreStats | null>(null);
  const [conversations, setConversations] = useState<ObservabilityConversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<string>("");
  const [runGroups, setRunGroups] = useState<ObservabilityRunGroup[]>([]);
  const [latestSnapshots, setLatestSnapshots] = useState<ObservabilitySnapshot[]>([]);
  const [loading, setLoading] = useState(true);
  const [obsLoading, setObsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    async function loadBaseMetrics() {
      setLoading(true);
      setError(null);
      try {
        const [coreResponse, conversationsResponse] = await Promise.all([
          requestPayload<CoreStats>("/api/core/stats/overview"),
          requestPayload<ObservabilityConversation[]>("/api/obs/v2/conversations"),
        ]);

        if (!mounted) {
          return;
        }

        setCoreStats(coreResponse.data);
        setConversations(conversationsResponse.data);
        if (conversationsResponse.data[0]) {
          setSelectedConversation(conversationsResponse.data[0].conversation_id);
        }
      } catch (loadError) {
        if (mounted) {
          setError(loadError instanceof Error ? loadError.message : "Failed to load metrics.");
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    void loadBaseMetrics();

    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    let mounted = true;

    async function loadObservedMetrics() {
      if (!selectedConversation) {
        setRunGroups([]);
        setLatestSnapshots([]);
        return;
      }

      setObsLoading(true);
      try {
        const [runGroupsResponse, latestResponse] = await Promise.all([
          requestPayload<RunGroupsResponse>(
            `/api/obs/v2/conversations/${selectedConversation}/telemetry/run_groups/recent?limit=1`,
          ),
          requestPayload<LatestResponse>(
            `/api/obs/v2/conversations/${selectedConversation}/telemetry/latest`,
          ),
        ]);

        if (!mounted) {
          return;
        }

        setRunGroups(runGroupsResponse.data.run_groups || []);
        setLatestSnapshots(latestResponse.data.snapshots || []);
      } catch (loadError) {
        if (mounted) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Failed to load observed telemetry payloads.",
          );
        }
      } finally {
        if (mounted) {
          setObsLoading(false);
        }
      }
    }

    void loadObservedMetrics();

    return () => {
      mounted = false;
    };
  }, [selectedConversation]);

  const currentRunGroup = runGroups[0] || null;
  const currentSnapshot = latestSnapshots[0] || null;
  const observedRunGroupEntries = currentRunGroup && isRecord(currentRunGroup)
    ? scalarEntries(currentRunGroup as Record<string, unknown>)
    : [];
  const observedMetricEntries = currentSnapshot && isRecord(currentSnapshot.metrics)
    ? scalarEntries(currentSnapshot.metrics)
    : [];

  return (
    <div className="stack">
      <PageHeader
        title="Observed Metrics"
        copy="Render current values only. This page surfaces the keys that are actually present in current Core and Observability JSON payloads without synthesizing new rollups."
      />

      <LoadState loading={loading} error={error} />

      {coreStats ? (
        <>
          <section className="metrics-grid">
            <article className="metric-card">
              <span className="label">Core total memories</span>
              <span className="value">{coreStats.total_memories.toLocaleString()}</span>
            </article>
            <article className="metric-card">
              <span className="label">Core total sessions</span>
              <span className="value">{coreStats.total_sessions.toLocaleString()}</span>
            </article>
            <article className="metric-card warn">
              <span className="label">Core recent writes (24h)</span>
              <span className="value">{coreStats.recent_writes_24h.toLocaleString()}</span>
            </article>
          </section>

          <section className="panel">
            <div className="control-grid">
              <div className="field">
                <label htmlFor="metrics-conversation">Observed conversation</label>
                <select
                  id="metrics-conversation"
                  onChange={(event) => setSelectedConversation(event.target.value)}
                  value={selectedConversation}
                >
                  {conversations.map((conversation) => (
                    <option key={conversation.conversation_id} value={conversation.conversation_id}>
                      {conversation.title} ({conversation.conversation_id.slice(0, 8)})
                    </option>
                  ))}
                </select>
              </div>
            </div>
            {obsLoading ? (
              <div className="note">Loading current Observability payloads…</div>
            ) : (
              <div className="status-line">
                <span className="pill">run_groups={runGroups.length}</span>
                <span className="pill">latest_snapshots={latestSnapshots.length}</span>
              </div>
            )}
          </section>

          <div className="grid-2">
            <section className="panel">
              <h2>Currently observed run-group keys</h2>
              {observedRunGroupEntries.length ? (
                <div className="key-grid">
                  {observedRunGroupEntries.map(([key, value]) => (
                    <div className="key-box" key={key}>
                      <strong>{key}</strong>
                      <div className="muted">{value}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty">
                  No current run-group scalar keys returned. This page only renders keys present in payloads.
                </div>
              )}
            </section>

            <section className="panel">
              <h2>Currently observed snapshot metric keys</h2>
              {observedMetricEntries.length ? (
                <div className="key-grid">
                  {observedMetricEntries.map(([key, value]) => (
                    <div className="key-box" key={key}>
                      <strong>{key}</strong>
                      <div className="muted">{value}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty">
                  No scalar snapshot metrics returned. Nested metrics remain visible in the raw payload panel.
                </div>
              )}
            </section>
          </div>

          <div className="grid-2">
            <JsonBlock title="Current run-group payload" value={currentRunGroup || {}} />
            <JsonBlock title="Current snapshot payload" value={currentSnapshot || {}} />
          </div>
        </>
      ) : null}
    </div>
  );
}

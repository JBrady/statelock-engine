"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

import { JsonBlock } from "@/components/json-block";
import { KeyValueGrid } from "@/components/key-value-grid";
import { LoadState } from "@/components/load-state";
import { PageHeader } from "@/components/page-header";
import { requestPayload } from "@/lib/client";
import { formatDateTime, formatMaybeJson, isRecord } from "@/lib/format";
import type {
  ObservabilityGovernanceLog,
  ObservabilitySnapshot,
  ObservabilitySpan,
  ObservabilityTurn,
} from "@/lib/types";

type SnapshotsResponse = { snapshots: ObservabilitySnapshot[] };
type ExplainResponse = Record<string, unknown>;

type ExplainMap = Record<string, ExplainResponse>;

export default function ObservabilityRunDetailPage() {
  const params = useParams<{ conversationId: string; runGroupId: string }>();
  const conversationId = params.conversationId;
  const runGroupId = params.runGroupId;

  const [snapshots, setSnapshots] = useState<ObservabilitySnapshot[]>([]);
  const [explains, setExplains] = useState<ExplainMap>({});
  const [spans, setSpans] = useState<ObservabilitySpan[]>([]);
  const [turns, setTurns] = useState<ObservabilityTurn[]>([]);
  const [governanceLog, setGovernanceLog] = useState<ObservabilityGovernanceLog[]>([]);
  const [selectedSpanId, setSelectedSpanId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    async function loadRunDetail() {
      setLoading(true);
      setError(null);
      try {
        const [detailResponse, spansResponse, turnsResponse, governanceResponse] =
          await Promise.all([
            requestPayload<SnapshotsResponse>(
              `/api/obs/v2/conversations/${conversationId}/telemetry/run_groups/${runGroupId}`,
            ),
            requestPayload<ObservabilitySpan[]>(
              `/api/obs/v2/conversations/${conversationId}/spans?include_quarantined=true`,
            ),
            requestPayload<ObservabilityTurn[]>(
              `/api/obs/v2/conversations/${conversationId}/turns`,
            ),
            requestPayload<ObservabilityGovernanceLog[]>(
              `/api/obs/v2/conversations/${conversationId}/governance/log`,
            ),
          ]);

        const explainEntries = await Promise.all(
          (detailResponse.data.snapshots || []).map(async (snapshot) => {
            const explainResponse = await requestPayload<ExplainResponse>(
              `/api/obs/v2/conversations/${conversationId}/telemetry/snapshots/${snapshot.snapshot_id}/explain`,
            );
            return [snapshot.snapshot_id, explainResponse.data] as const;
          }),
        );

        if (!mounted) {
          return;
        }

        setSnapshots(detailResponse.data.snapshots || []);
        setExplains(Object.fromEntries(explainEntries));
        setSpans(spansResponse.data || []);
        setTurns(turnsResponse.data || []);
        setGovernanceLog(governanceResponse.data || []);

        const firstWeight = detailResponse.data.snapshots
          ?.flatMap((snapshot) => snapshot.influence.weights || [])
          .find((weight) => typeof weight.span_id === "string");
        setSelectedSpanId(typeof firstWeight?.span_id === "string" ? firstWeight.span_id : null);
      } catch (loadError) {
        if (mounted) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Failed to load run-group detail.",
          );
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    void loadRunDetail();

    return () => {
      mounted = false;
    };
  }, [conversationId, runGroupId]);

  const spanLookup = new Map<string, ObservabilitySpan>();
  for (const span of spans) {
    spanLookup.set(span.span_id, span);
  }

  const turnLookup = new Map<string, ObservabilityTurn>();
  for (const turn of turns) {
    turnLookup.set(turn.turn_id, turn);
  }

  const selectedSpan = selectedSpanId ? spanLookup.get(selectedSpanId) || null : null;

  const groups = new Map<string, Array<Record<string, unknown>>>();
  for (const snapshot of snapshots) {
    for (const weight of snapshot.influence.weights || []) {
      const threadId =
        typeof weight.thread_id === "string" ? weight.thread_id : "unassigned";
      const existing = groups.get(threadId) || [];
      existing.push({
        ...weight,
        snapshot_id: snapshot.snapshot_id,
        method: snapshot.method,
      });
      groups.set(threadId, existing);
    }
  }
  const groupedWeights = Array.from(groups.entries()).sort(([a], [b]) =>
    a.localeCompare(b),
  );

  return (
    <div className="stack">
      <PageHeader
        title="Observability Run Detail"
        copy="Render run-group detail first, then enrich it with explain payloads, span drill-in, and governance history when those auxiliary endpoints return data."
        actions={
          <Link className="link-button" href="/obs/runs">
            Back to runs
          </Link>
        }
      />

      <LoadState
        loading={loading}
        error={error}
        empty={!loading && !snapshots.length ? "No snapshots returned for this run group." : null}
      />

      {snapshots.length ? (
        <>
          <section className="metrics-grid">
            <article className="metric-card">
              <span className="label">Conversation</span>
              <span className="subvalue mono">{conversationId}</span>
            </article>
            <article className="metric-card">
              <span className="label">Run group</span>
              <span className="subvalue mono">{runGroupId}</span>
            </article>
            <article className="metric-card warn">
              <span className="label">Snapshots</span>
              <span className="value">{snapshots.length}</span>
            </article>
          </section>

          <div className="tree-grid">
            <section className="panel">
              <h2>Span influence by thread</h2>
              {groupedWeights.length ? (
                groupedWeights.map(([threadId, weights]) => (
                  <div className="thread-group" key={threadId}>
                    <div className="header-bar">
                      <h3>{threadId}</h3>
                      <span className="pill">{weights.length} rows</span>
                    </div>
                    {weights.map((weight, index) => {
                      const spanId =
                        typeof weight.span_id === "string" ? weight.span_id : `unknown-${index}`;
                      return (
                        <button
                          className={`tree-row${selectedSpanId === spanId ? " active" : ""}`}
                          key={`${threadId}-${spanId}-${String(weight.snapshot_id)}`}
                          onClick={() => setSelectedSpanId(spanId)}
                          type="button"
                        >
                          <strong>{spanId}</strong>
                          <div className="row-meta">
                            <span>method={String(weight.method || "n/a")}</span>
                            <span>w={String(weight.w ?? "n/a")}</span>
                            <span>raw={String(weight.raw_score ?? "n/a")}</span>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                ))
              ) : (
                <div className="empty">No influence weights returned for this run group.</div>
              )}
            </section>

            <section className="detail-card">
              <h2>Selected span detail</h2>
              {selectedSpan ? (
                <div className="stack">
                  <div className="list-item">
                    <h3>{selectedSpan.span_id}</h3>
                    <p className="muted">{selectedSpan.text}</p>
                    <div className="row-meta">
                      <span>thread={selectedSpan.thread_id}</span>
                      <span>created={formatDateTime(selectedSpan.created_at)}</span>
                      <span>quarantined={selectedSpan.quarantined_until || "no"}</span>
                    </div>
                  </div>
                  <section className="panel">
                    <h3>Trust + recency</h3>
                    <KeyValueGrid
                      record={{
                        ...(isRecord(selectedSpan.trust) ? selectedSpan.trust : {}),
                        ...(isRecord(selectedSpan.recency) ? selectedSpan.recency : {}),
                      }}
                    />
                  </section>
                  <section className="panel">
                    <h3>Source turns</h3>
                    {selectedSpan.source_turn_ids.length ? (
                      <div className="list">
                        {selectedSpan.source_turn_ids.map((turnId) => {
                          const turn = turnLookup.get(turnId);
                          return (
                            <article className="list-item" key={turnId}>
                              <h3>{turn?.speaker || "turn"} · {turnId}</h3>
                              <p className="muted">{turn?.text || "Turn not returned by /turns."}</p>
                            </article>
                          );
                        })}
                      </div>
                    ) : (
                      <div className="empty">No source turns linked to this span.</div>
                    )}
                  </section>
                </div>
              ) : (
                <div className="empty">Select a span row to inspect its full detail.</div>
              )}
            </section>
          </div>

          <div className="grid-2">
            <section className="panel">
              <h2>Snapshot sections</h2>
              <div className="list">
                {snapshots.map((snapshot) => (
                  <article className="list-item" key={snapshot.snapshot_id}>
                    <div className="header-bar">
                      <h3>{snapshot.method}</h3>
                      <span className="pill">{formatDateTime(snapshot.created_at)}</span>
                    </div>
                    <p className="muted">
                      target_thread={snapshot.target_thread_id} · proxy_kind={snapshot.proxy_kind || "n/a"}
                    </p>
                    <div className="row-meta">
                      <span>snapshot={snapshot.snapshot_id}</span>
                      <span>spans_considered={snapshot.spans_considered.length}</span>
                    </div>
                    <div className="json-block" style={{ marginTop: "12px" }}>
                      <pre>{formatMaybeJson(explains[snapshot.snapshot_id] || snapshot.metrics)}</pre>
                    </div>
                  </article>
                ))}
              </div>
            </section>

            <section className="panel">
              <h2>Governance + auxiliary data</h2>
              {governanceLog.length ? (
                <div className="list">
                  {governanceLog.map((item) => (
                    <article className="list-item" key={item.event_id}>
                      <div className="header-bar">
                        <h3>{item.event_type}</h3>
                        <span className="pill warn">{formatDateTime(item.created_at)}</span>
                      </div>
                      <p className="muted">snapshot={item.snapshot_id || "n/a"}</p>
                      <div className="json-block" style={{ marginTop: "12px" }}>
                        <pre>{formatMaybeJson(item.details)}</pre>
                      </div>
                    </article>
                  ))}
                </div>
              ) : (
                <div className="empty">
                  Governance log returned no rows. The page still renders run-group and snapshot detail.
                </div>
              )}
            </section>
          </div>

          <div className="grid-2">
            <JsonBlock title="Raw snapshots" value={snapshots} />
            <JsonBlock title="Raw spans" value={spans} />
          </div>
        </>
      ) : null}
    </div>
  );
}

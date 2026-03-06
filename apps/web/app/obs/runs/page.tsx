"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { JsonBlock } from "@/components/json-block";
import { LoadState } from "@/components/load-state";
import { PageHeader } from "@/components/page-header";
import { requestPayload } from "@/lib/client";
import { formatDateTime, formatNumber } from "@/lib/format";
import type {
  ObservabilityConversation,
  ObservabilityRunGroup,
  ObservabilitySnapshot,
} from "@/lib/types";

type ConversationsResponse = ObservabilityConversation[];
type RunGroupsResponse = { run_groups: ObservabilityRunGroup[] };
type LatestResponse = { snapshots: ObservabilitySnapshot[] };

export default function ObservabilityRunsPage() {
  const [conversations, setConversations] = useState<ObservabilityConversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<string>("");
  const [runGroups, setRunGroups] = useState<ObservabilityRunGroup[]>([]);
  const [latestSnapshots, setLatestSnapshots] = useState<ObservabilitySnapshot[]>([]);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    async function loadConversations() {
      setLoading(true);
      setError(null);
      try {
        const response = await requestPayload<ConversationsResponse>("/api/obs/v2/conversations");
        if (!mounted) {
          return;
        }
        setConversations(response.data);
        if (response.data[0]) {
          setSelectedConversation(response.data[0].conversation_id);
        }
      } catch (loadError) {
        if (mounted) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Failed to load Observability conversations.",
          );
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    void loadConversations();

    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    let mounted = true;

    async function loadRunData() {
      if (!selectedConversation) {
        setRunGroups([]);
        setLatestSnapshots([]);
        return;
      }

      setDetailLoading(true);
      setError(null);

      try {
        const [runGroupsResponse, latestResponse] = await Promise.all([
          requestPayload<RunGroupsResponse>(
            `/api/obs/v2/conversations/${selectedConversation}/telemetry/run_groups/recent?limit=20`,
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
              : "Failed to load run-group data.",
          );
          setRunGroups([]);
          setLatestSnapshots([]);
        }
      } finally {
        if (mounted) {
          setDetailLoading(false);
        }
      }
    }

    void loadRunData();

    return () => {
      mounted = false;
    };
  }, [selectedConversation]);

  return (
    <div className="stack">
      <PageHeader
        title="Observability Runs"
        copy="Use the existing conversation-scoped run-group endpoints. This page intentionally does not pretend there is a global runs index when the backend does not expose one."
      />

      <LoadState
        loading={loading}
        error={error}
        empty={!loading && !conversations.length ? "No conversations returned yet. Run the Observability seed/demo flow first." : null}
      />

      {conversations.length ? (
        <>
          <section className="panel">
            <div className="control-grid">
              <div className="field">
                <label htmlFor="conversation">Conversation</label>
                <select
                  id="conversation"
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
            <div className="status-line">
              <span className="pill">{conversations.length} conversations loaded</span>
              <span className="pill warn">
                selected={selectedConversation ? selectedConversation.slice(0, 12) : "none"}
              </span>
            </div>
          </section>

          <LoadState
            loading={detailLoading}
            empty={
              !detailLoading && selectedConversation && !runGroups.length
                ? "No run groups for the selected conversation yet."
                : null
            }
          />

          {runGroups.length ? (
            <section className="table-wrap">
              <h2>Recent run groups</h2>
              <table>
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>Run group</th>
                    <th>Target thread</th>
                    <th>Coverage</th>
                    <th>Observed metrics</th>
                    <th>Detail</th>
                  </tr>
                </thead>
                <tbody>
                  {runGroups.map((group) => (
                    <tr key={group.run_group_id}>
                      <td>{formatDateTime(group.created_at_max)}</td>
                      <td>
                        <code>{group.run_group_id}</code>
                      </td>
                      <td>{group.target_thread_id || "n/a"}</td>
                      <td>
                        <div className="row-meta">
                          <span>proxy={String(Boolean(group.has_proxy))}</span>
                          <span>ablation={String(Boolean(group.has_ablation))}</span>
                        </div>
                      </td>
                      <td>
                        <div className="row-meta">
                          <span>Coff={formatNumber(group.Coff)}</span>
                          <span>H={formatNumber(group.H)}</span>
                        </div>
                      </td>
                      <td>
                        <Link
                          className="link-button"
                          href={`/obs/runs/${selectedConversation}/${group.run_group_id}`}
                        >
                          Open run detail
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          ) : null}

          <div className="grid-2">
            <JsonBlock
              title="Latest snapshots"
              value={latestSnapshots.length ? latestSnapshots : { snapshots: [] }}
            />
            <JsonBlock
              title="Run group payload"
              value={{ conversation_id: selectedConversation, run_groups: runGroups }}
            />
          </div>
        </>
      ) : null}
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";

import { JsonBlock } from "@/components/json-block";
import { LoadState } from "@/components/load-state";
import { PageHeader } from "@/components/page-header";
import { requestPayload } from "@/lib/client";
import { formatDateTime } from "@/lib/format";
import type { CoreMemory, CoreSession } from "@/lib/types";

type SessionsResponse = {
  items: CoreSession[];
  total: number;
  limit: number;
  offset: number;
};

type MemoriesResponse = {
  items: CoreMemory[];
  total?: number;
  limit: number;
  offset: number;
};

export default function CoreSessionsPage() {
  const [sessions, setSessions] = useState<CoreSession[]>([]);
  const [selectedSession, setSelectedSession] = useState<string>("");
  const [memories, setMemories] = useState<CoreMemory[]>([]);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    async function loadSessions() {
      setLoading(true);
      setError(null);

      try {
        const response = await requestPayload<SessionsResponse>(
          "/api/core/sessions?limit=20&offset=0",
        );
        if (!mounted) {
          return;
        }
        setSessions(response.data.items);
        if (response.data.items[0]) {
          setSelectedSession(response.data.items[0].session_id);
        }
      } catch (loadError) {
        if (mounted) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Failed to load sessions.",
          );
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    void loadSessions();

    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    let mounted = true;

    async function loadSessionMemories() {
      if (!selectedSession) {
        setMemories([]);
        return;
      }

      setDetailLoading(true);
      try {
        const params = new URLSearchParams({
          session_id: selectedSession,
          limit: "30",
          offset: "0",
        });
        const response = await requestPayload<MemoriesResponse>(
          `/api/core/memories?${params.toString()}`,
        );
        if (mounted) {
          setMemories(response.data.items);
        }
      } catch (loadError) {
        if (mounted) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Failed to load session memories.",
          );
          setMemories([]);
        }
      } finally {
        if (mounted) {
          setDetailLoading(false);
        }
      }
    }

    void loadSessionMemories();

    return () => {
      mounted = false;
    };
  }, [selectedSession]);

  return (
    <div className="stack">
      <PageHeader
        title="Core Sessions"
        copy="Browse current sessions from the Insights endpoints and drill into the exact memory items backing a selected session."
      />

      <LoadState
        loading={loading}
        error={error}
        empty={!loading && !sessions.length ? "No sessions returned yet. Seed Core memory first." : null}
      />

      {sessions.length ? (
        <div className="split-grid">
          <section className="table-wrap">
            <h2>Session inventory</h2>
            <table>
              <thead>
                <tr>
                  <th>Session</th>
                  <th>Memory count</th>
                  <th>Last updated</th>
                </tr>
              </thead>
              <tbody>
                {sessions.map((session) => (
                  <tr
                    key={session.session_id}
                    onClick={() => setSelectedSession(session.session_id)}
                    style={{ cursor: "pointer" }}
                  >
                    <td>
                      <strong>{session.session_id}</strong>
                    </td>
                    <td>{session.memory_count}</td>
                    <td>{formatDateTime(session.last_updated)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="panel">
            <h2>Selected session</h2>
            <p className="muted">{selectedSession || "No session selected."}</p>
            {detailLoading ? (
              <div className="note">Loading session memories…</div>
            ) : !memories.length ? (
              <div className="empty">No memories found for the selected session.</div>
            ) : (
              <div className="list">
                {memories.map((memory) => (
                  <article className="list-item" key={memory.id}>
                    <h3>{memory.name || "Unnamed memory"}</h3>
                    <p className="muted">{memory.content}</p>
                    <div className="row-meta">
                      <span>{memory.id}</span>
                      <span>updated={formatDateTime(memory.updated_at)}</span>
                      <span>tags={(memory.tags || []).join(", ") || "none"}</span>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
        </div>
      ) : null}

      <JsonBlock title="Current session payload" value={{ sessions, selectedSession, memories }} />
    </div>
  );
}

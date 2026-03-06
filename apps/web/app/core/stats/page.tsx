"use client";

import { useEffect, useState } from "react";

import { JsonBlock } from "@/components/json-block";
import { LoadState } from "@/components/load-state";
import { PageHeader } from "@/components/page-header";
import { requestPayload } from "@/lib/client";
import { formatDateTime } from "@/lib/format";
import type { CoreSession, CoreStats } from "@/lib/types";

type SessionsResponse = {
  items: CoreSession[];
};

export default function CoreStatsPage() {
  const [stats, setStats] = useState<CoreStats | null>(null);
  const [sessions, setSessions] = useState<CoreSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    async function loadStats() {
      setLoading(true);
      setError(null);
      try {
        const [statsResponse, sessionsResponse] = await Promise.all([
          requestPayload<CoreStats>("/api/core/stats/overview"),
          requestPayload<SessionsResponse>("/api/core/sessions?limit=8&offset=0"),
        ]);

        if (!mounted) {
          return;
        }

        setStats(statsResponse.data);
        setSessions(sessionsResponse.data.items);
      } catch (loadError) {
        if (mounted) {
          setError(loadError instanceof Error ? loadError.message : "Failed to load stats.");
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    void loadStats();

    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="stack">
      <PageHeader
        title="Core Stats Overview"
        copy="Mirror the existing static console spec: total memories, total sessions, recent writes, top tags, and a compact recent-session view."
      />

      <LoadState loading={loading} error={error} />

      {stats ? (
        <>
          <section className="metrics-grid">
            <article className="metric-card">
              <span className="label">Total memories</span>
              <span className="value">{stats.total_memories.toLocaleString()}</span>
            </article>
            <article className="metric-card">
              <span className="label">Total sessions</span>
              <span className="value">{stats.total_sessions.toLocaleString()}</span>
            </article>
            <article className="metric-card warn">
              <span className="label">Recent writes (24h)</span>
              <span className="value">{stats.recent_writes_24h.toLocaleString()}</span>
            </article>
          </section>

          <div className="grid-2">
            <section className="table-wrap">
              <h2>Top tags</h2>
              <table>
                <thead>
                  <tr>
                    <th>Tag</th>
                    <th>Count</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.top_tags.map((tag) => (
                    <tr key={tag.tag}>
                      <td>
                        <span className="pill">{tag.tag}</span>
                      </td>
                      <td>{tag.count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>

            <section className="table-wrap">
              <h2>Recent sessions</h2>
              <table>
                <thead>
                  <tr>
                    <th>Session</th>
                    <th>Count</th>
                    <th>Last updated</th>
                  </tr>
                </thead>
                <tbody>
                  {sessions.map((session) => (
                    <tr key={session.session_id}>
                      <td>{session.session_id}</td>
                      <td>{session.memory_count}</td>
                      <td>{formatDateTime(session.last_updated)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          </div>

          <JsonBlock title="Stats payload" value={{ stats, sessions }} />
        </>
      ) : null}
    </div>
  );
}

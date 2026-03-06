"use client";

import { useEffect, useState } from "react";

import { JsonBlock } from "@/components/json-block";
import { LoadState } from "@/components/load-state";
import { PageHeader } from "@/components/page-header";
import { requestPayload } from "@/lib/client";
import { formatMaybeJson } from "@/lib/format";

type HealthData = {
  health?: unknown;
  ready?: unknown;
  headers?: Record<string, string | null>;
};

export default function CoreHealthPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<HealthData | null>(null);

  useEffect(() => {
    let mounted = true;

    async function load() {
      setLoading(true);
      setError(null);

      try {
        const [health, ready] = await Promise.all([
          requestPayload("/api/core/healthz"),
          requestPayload("/api/core/readyz"),
        ]);

        if (!mounted) {
          return;
        }

        setData({
          health: health.data,
          ready: ready.data,
          headers: health.headers,
        });
      } catch (loadError) {
        if (!mounted) {
          return;
        }
        setError(loadError instanceof Error ? loadError.message : "Failed to load Core health state.");
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    void load();

    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="stack">
      <PageHeader
        title="Core Health"
        copy="Read the public health and readiness endpoints, plus passthrough trace/version headers from the Core proxy."
      />

      <LoadState loading={loading} error={error} />

      {data ? (
        <>
          <section className="metrics-grid">
            <article className="metric-card">
              <span className="label">/healthz</span>
              <span className="value">{formatMaybeJson(data.health)}</span>
            </article>
            <article className="metric-card">
              <span className="label">/readyz</span>
              <span className="value">{formatMaybeJson(data.ready)}</span>
            </article>
            <article className="metric-card warn">
              <span className="label">Passthrough headers</span>
              <span className="subvalue">
                trace_id={data.headers?.["x-trace-id"] || "n/a"}
              </span>
              <span className="subvalue">
                version={data.headers?.["x-statelock-version"] || "n/a"}
              </span>
            </article>
          </section>

          <div className="grid-2">
            <JsonBlock title="Health payloads" value={{ health: data.health, ready: data.ready }} />
            <JsonBlock title="Header snapshot" value={data.headers} />
          </div>
        </>
      ) : null}
    </div>
  );
}

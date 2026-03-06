"use client";

import { useState } from "react";

import { JsonBlock } from "@/components/json-block";
import { PageHeader } from "@/components/page-header";
import { requestPayload } from "@/lib/client";
import type { CoreMemory } from "@/lib/types";

type QueryResponse = {
  results: CoreMemory[];
};

export default function CoreQueryPage() {
  const [queryText, setQueryText] = useState("what did we decide about cloud fallback");
  const [sessionId, setSessionId] = useState("agent:chat:main");
  const [topK, setTopK] = useState("5");
  const [candidateK, setCandidateK] = useState("20");
  const [similarityWeight, setSimilarityWeight] = useState("0.75");
  const [recencyWeight, setRecencyWeight] = useState("0.25");
  const [mode, setMode] = useState<"standard" | "hybrid">("hybrid");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [payload, setPayload] = useState<QueryResponse | null>(null);
  const [headers, setHeaders] = useState<Record<string, string | null> | null>(null);

  async function runQuery() {
    setLoading(true);
    setError(null);

    const requestBody: Record<string, unknown> = {
      query_text: queryText,
      session_id: sessionId || null,
      top_k: Number(topK || 5),
    };

    let path = "/api/core/memories/query";
    if (mode === "hybrid") {
      path = "/api/core/memories/query-hybrid";
      requestBody.candidate_k = Number(candidateK || 20);
      requestBody.similarity_weight = Number(similarityWeight || 0.75);
      requestBody.recency_weight = Number(recencyWeight || 0.25);
    }

    try {
      const response = await requestPayload<QueryResponse>(path, {
        method: "POST",
        headers: {
          "content-type": "application/json",
        },
        body: JSON.stringify(requestBody),
      });

      setPayload(response.data);
      setHeaders(response.headers);
    } catch (queryError) {
      setError(queryError instanceof Error ? queryError.message : "Query failed.");
      setPayload(null);
      setHeaders(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="stack">
      <PageHeader
        title="Core Query Playground"
        copy="Match the existing Core console behavior: switch between standard and hybrid query, keep the query payload visible, and inspect returned trace/version headers."
        actions={
          <>
            <button className="ghost-button" onClick={() => setMode("standard")} type="button">
              Standard
            </button>
            <button className="button" onClick={() => setMode("hybrid")} type="button">
              Hybrid
            </button>
          </>
        }
      />

      <div className="split-grid">
        <section className="panel">
          <h2>Query form</h2>
          <div className="controls">
            <div className="field">
              <label htmlFor="query-text">Query text</label>
              <textarea
                id="query-text"
                onChange={(event) => setQueryText(event.target.value)}
                value={queryText}
              />
            </div>
            <div className="control-grid">
              <div className="field">
                <label htmlFor="session-id">Session id</label>
                <input
                  id="session-id"
                  onChange={(event) => setSessionId(event.target.value)}
                  value={sessionId}
                />
              </div>
              <div className="field">
                <label htmlFor="top-k">Top K</label>
                <input
                  id="top-k"
                  min="1"
                  onChange={(event) => setTopK(event.target.value)}
                  type="number"
                  value={topK}
                />
              </div>
            </div>
            {mode === "hybrid" ? (
              <div className="control-grid compact">
                <div className="field">
                  <label htmlFor="candidate-k">Candidate K</label>
                  <input
                    id="candidate-k"
                    min="1"
                    onChange={(event) => setCandidateK(event.target.value)}
                    type="number"
                    value={candidateK}
                  />
                </div>
                <div className="field">
                  <label htmlFor="similarity-weight">Similarity weight</label>
                  <input
                    id="similarity-weight"
                    max="1"
                    min="0"
                    onChange={(event) => setSimilarityWeight(event.target.value)}
                    step="0.05"
                    type="number"
                    value={similarityWeight}
                  />
                </div>
                <div className="field">
                  <label htmlFor="recency-weight">Recency weight</label>
                  <input
                    id="recency-weight"
                    max="1"
                    min="0"
                    onChange={(event) => setRecencyWeight(event.target.value)}
                    step="0.05"
                    type="number"
                    value={recencyWeight}
                  />
                </div>
              </div>
            ) : null}
            <div className="toolbar">
              <button className="button" disabled={loading} onClick={runQuery} type="button">
                {loading ? "Running…" : "Run query"}
              </button>
            </div>
            {error ? <div className="error">{error}</div> : null}
            {headers ? (
              <div className="status-line">
                <span className="pill">trace={headers["x-trace-id"] || "n/a"}</span>
                <span className="pill">version={headers["x-statelock-version"] || "n/a"}</span>
              </div>
            ) : null}
          </div>
        </section>

        <section className="panel">
          <h2>Results</h2>
          {!payload?.results?.length ? (
            <div className="empty">
              {loading ? "Waiting for query results…" : "No query results yet. Seed Core memory first if needed."}
            </div>
          ) : (
            <div className="list">
              {payload.results.map((result) => (
                <article className="list-item" key={result.id}>
                  <div className="header-bar">
                    <h3>{result.name || "Unnamed memory"}</h3>
                    <span className="pill">{result.session_id}</span>
                  </div>
                  <p className="muted">{result.content}</p>
                  <div className="row-meta">
                    <span>score={result.score ?? "n/a"}</span>
                    <span>distance={result.distance ?? "n/a"}</span>
                    <span>tags={(result.tags || []).join(", ") || "none"}</span>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>

      <JsonBlock title="Response payload" value={payload || { results: [] }} />
    </div>
  );
}

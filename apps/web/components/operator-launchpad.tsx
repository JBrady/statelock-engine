import Link from "next/link";

export function OperatorLaunchpad() {
  return (
    <div className="stack">
      <section className="hero-card">
        <div className="hero-grid">
          <div>
            <p className="eyebrow">Two-track operator surface</p>
            <h1>Inspect memory state and trace-like agent runs without backend coupling.</h1>
            <p>
              This app proxies Core and Observability separately, keeps credentials
              server-side, and mirrors the existing repo boundaries instead of
              flattening them together.
            </p>
            <div className="status-line">
              <span className="pill">Core proxy: /api/core/*</span>
              <span className="pill">Obs proxy: /api/obs/*</span>
              <span className="pill warn">No cross-track backend wiring</span>
            </div>
          </div>
          <div className="hero-points">
            <div className="hero-point">
              <strong>Core Track</strong>
              Health, query playground, sessions, tags, and stats driven by the
              same endpoints already exercised by the static console.
            </div>
            <div className="hero-point">
              <strong>Observability Track</strong>
              Conversation-scoped run groups, snapshot explainability, span drill-in,
              and governance history via legacy `/v2/*` routes.
            </div>
            <div className="hero-point">
              <strong>Current-value metrics only</strong>
              The UI renders confirmed payload keys from existing backends and does
              not invent time series or synthetic rollups.
            </div>
          </div>
        </div>
      </section>

      <section className="link-grid">
        <Link className="link-card" href="/core/query">
          <strong>Core Query Playground</strong>
          <p>Run standard or hybrid memory queries and inspect passthrough headers.</p>
        </Link>
        <Link className="link-card" href="/core/stats">
          <strong>Core Stats Overview</strong>
          <p>See totals, recent writes, top tags, and recent sessions.</p>
        </Link>
        <Link className="link-card" href="/obs/runs">
          <strong>Observability Runs</strong>
          <p>Select a conversation and inspect current run groups without coupling the backends.</p>
        </Link>
        <Link className="link-card" href="/metrics">
          <strong>Observed Metrics</strong>
          <p>Render only keys actually returned by the current Core and Observability payloads.</p>
        </Link>
      </section>

      <section className="panel">
        <h2>Development notes</h2>
        <div className="list">
          <div className="list-item">
            <h3>Core seed path</h3>
            <p className="muted">
              Use the existing Core examples to create memories for session
              <span className="inline-code"> agent:chat:main</span>, then verify
              with <span className="inline-code">GET /api/core/memories</span>.
            </p>
          </div>
          <div className="list-item">
            <h3>Observability seed path</h3>
            <p className="muted">
              Use the demo/seed flow in <span className="inline-code">experimental/observability</span>
              to create a conversation and run groups before verifying the run pages.
            </p>
          </div>
          <div className="list-item">
            <h3>Proxy behavior</h3>
            <p className="muted">
              Status codes, response bodies, and allowed response headers are passed
              through from upstream. The proxy does not rewrite data into a shared schema.
            </p>
          </div>
        </div>
        <p className="footer-note">
          Package manager for this isolated app: <span className="inline-code">npm</span>.
        </p>
      </section>
    </div>
  );
}

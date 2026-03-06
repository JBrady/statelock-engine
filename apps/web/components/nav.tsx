"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

type NavEntry = {
  href: string;
  label: string;
  hint: string;
};

const navGroups: Array<{ label: string; entries: NavEntry[] }> = [
  {
    label: "Overview",
    entries: [
      { href: "/", label: "Launchpad", hint: "Tracks, constraints, run hints" },
      { href: "/metrics", label: "Metrics", hint: "Current counters and observed keys" },
    ],
  },
  {
    label: "Core Track",
    entries: [
      { href: "/core/health", label: "Health", hint: "Readiness and request headers" },
      { href: "/core/query", label: "Query", hint: "Query + hybrid playground" },
      { href: "/core/sessions", label: "Sessions", hint: "Session inventory and memory drill-in" },
      { href: "/core/tags", label: "Tags", hint: "Tag counts and current labels" },
      { href: "/core/stats", label: "Stats", hint: "Totals, top tags, recent sessions" },
    ],
  },
  {
    label: "Observability",
    entries: [
      { href: "/obs/runs", label: "Runs", hint: "Conversation-scoped run groups" },
    ],
  },
];

export function Nav() {
  const pathname = usePathname();

  return (
    <aside className="sidebar">
      <div className="brand-block">
        <p className="eyebrow">StateLock Rehydration</p>
        <h1 className="brand-title">Unified operator view</h1>
        <p className="brand-copy">
          Thin Next.js surface for Core memory operations and Observability trace
          inspection, with no backend coupling.
        </p>
      </div>

      {navGroups.map((group) => (
        <div className="nav-group" key={group.label}>
          <span className="nav-label">{group.label}</span>
          {group.entries.map((entry) => {
            const isActive =
              pathname === entry.href ||
              (entry.href !== "/" && pathname.startsWith(entry.href));

            return (
              <Link
                className={`nav-link${isActive ? " active" : ""}`}
                href={entry.href}
                key={entry.href}
              >
                <strong>{entry.label}</strong>
                <span>{entry.hint}</span>
              </Link>
            );
          })}
        </div>
      ))}
    </aside>
  );
}

"use client";

import { Activity, BrainCircuit, GitBranchPlus, House, MemoryStick, SlidersHorizontal, Sparkles, Waypoints } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

const navEntries = [
  { href: "/", label: "Overview", icon: House },
  { href: "/conversations", label: "Conversations", icon: BrainCircuit },
  { href: "/highlights", label: "Highlights", icon: Sparkles },
  { href: "/memory", label: "Memory", icon: MemoryStick },
  { href: "/relationships", label: "Relationships", icon: Waypoints },
  { href: "/runs", label: "Runs", icon: Activity },
  { href: "/learning-mode", label: "Learning Mode", icon: SlidersHorizontal },
];

export function ProductShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(14,118,110,0.18),_transparent_28%),radial-gradient(circle_at_top_right,_rgba(212,163,115,0.24),_transparent_22%),linear-gradient(180deg,#f7f3eb_0%,#eef6ef_100%)] px-4 py-5 sm:px-6 lg:px-8">
      <div className="mx-auto grid max-w-7xl gap-6 lg:grid-cols-[290px_minmax(0,1fr)]">
        <aside className="rounded-[2rem] border border-black/10 bg-[#163038] px-5 py-6 text-white shadow-product lg:sticky lg:top-6 lg:h-[calc(100vh-3rem)]">
          <div className="rounded-[1.6rem] border border-white/10 bg-white/5 p-5">
            <div className="inline-flex items-center rounded-full border border-white/10 bg-white/10 px-3 py-1 text-[0.7rem] uppercase tracking-[0.2em] text-white/70">
              StateLock product UI
            </div>
            <h1 className="mt-4 font-display text-3xl leading-tight">
              Continuity made legible for humans.
            </h1>
            <p className="mt-3 text-sm leading-6 text-white/72">
              Follow what happened, what StateLock noticed, what it kept, and how
              those decisions connect across Core and Observability.
            </p>
          </div>

          <nav className="mt-6 space-y-2">
            {navEntries.map((entry) => {
              const isActive =
                pathname === entry.href ||
                (entry.href !== "/" && pathname.startsWith(entry.href));
              const Icon = entry.icon;

              return (
                <Link
                  className={cn(
                    "flex items-center gap-3 rounded-2xl px-4 py-3 text-sm transition",
                    isActive
                      ? "bg-white text-[#163038]"
                      : "bg-white/0 text-white/75 hover:bg-white/8 hover:text-white",
                  )}
                  href={entry.href}
                  key={entry.href}
                >
                  <Icon className="h-4 w-4" />
                  <span>{entry.label}</span>
                </Link>
              );
            })}
          </nav>

          <div className="mt-6 rounded-[1.6rem] border border-white/10 bg-white/5 p-5 text-sm text-white/70">
            <p className="font-display text-lg text-white">Keep the seams visible</p>
            <p className="mt-2 leading-6">
              Core stays narrow. Observability owns richer continuity logic. The UI
              makes that distinction explicit instead of flattening it away.
            </p>
            <Link
              className="mt-4 inline-flex items-center gap-2 text-white"
              href="/operator"
            >
              <GitBranchPlus className="h-4 w-4" />
              Operator tools
            </Link>
          </div>
        </aside>

        <main className="min-w-0">{children}</main>
      </div>
    </div>
  );
}

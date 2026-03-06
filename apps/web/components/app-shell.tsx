"use client";

import type { ReactNode } from "react";
import { usePathname } from "next/navigation";

import { Nav } from "@/components/nav";
import { ProductShell } from "@/components/product-shell";
import { QueryProvider } from "@/components/query-provider";

function isOperatorPath(pathname: string) {
  return (
    pathname.startsWith("/core") ||
    pathname.startsWith("/obs") ||
    pathname.startsWith("/metrics") ||
    pathname.startsWith("/operator")
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  return (
    <QueryProvider>
      {isOperatorPath(pathname) ? (
        <div className="app-shell">
          <div className="chrome">
            <Nav />
            <main className="main">{children}</main>
          </div>
        </div>
      ) : (
        <ProductShell>{children}</ProductShell>
      )}
    </QueryProvider>
  );
}

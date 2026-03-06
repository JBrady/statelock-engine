import type { Metadata } from "next";
import type { ReactNode } from "react";

import { Nav } from "@/components/nav";

import "./globals.css";

export const metadata: Metadata = {
  title: "StateLock Unified UI",
  description: "Thin Next.js operator UI for StateLock Core and Observability.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="app-shell">
          <div className="chrome">
            <Nav />
            <main className="main">{children}</main>
          </div>
        </div>
      </body>
    </html>
  );
}

"use client";

import { LoaderCircle } from "lucide-react";
import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function ProductPageHeader({
  eyebrow,
  title,
  copy,
  actions,
}: {
  eyebrow: string;
  title: string;
  copy: string;
  actions?: ReactNode;
}) {
  return (
    <section className="rounded-[2rem] border border-black/10 bg-[#f8f4ec]/90 p-6 shadow-product">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-3xl">
          <Badge className="border-moss/20 bg-moss/10 text-moss">{eyebrow}</Badge>
          <h1 className="mt-4 font-display text-4xl leading-tight text-ink">{title}</h1>
          <p className="mt-3 text-base leading-7 text-black/65">{copy}</p>
        </div>
        {actions ? <div className="shrink-0">{actions}</div> : null}
      </div>
    </section>
  );
}

export function ProductEmptyState({
  title,
  copy,
}: {
  title: string;
  copy: string;
}) {
  return (
    <Card className="border-dashed bg-white/60">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{copy}</CardDescription>
      </CardHeader>
    </Card>
  );
}

export function ProductLoadingState({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex min-h-[200px] items-center justify-center rounded-[2rem] border border-black/10 bg-white/65 shadow-product">
      <div className="flex items-center gap-3 text-black/60">
        <LoaderCircle className="h-5 w-5 animate-spin" />
        <span>{label}</span>
      </div>
    </div>
  );
}

export function ProductErrorState({ message }: { message: string }) {
  return (
    <Card className="border-rust/20 bg-rust/5">
      <CardHeader>
        <CardTitle className="text-rust">Something needs attention</CardTitle>
        <CardDescription className="text-rust/80">{message}</CardDescription>
      </CardHeader>
    </Card>
  );
}

export function ProductMetric({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: ReactNode;
  tone?: "default" | "warning" | "good";
}) {
  return (
    <Card
      className={cn(
        tone === "warning" && "bg-clay/10",
        tone === "good" && "bg-moss/10",
      )}
    >
      <CardContent className="p-6">
        <p className="text-sm uppercase tracking-[0.14em] text-black/55">{label}</p>
        <div className="mt-3 font-display text-4xl text-ink">{value}</div>
      </CardContent>
    </Card>
  );
}

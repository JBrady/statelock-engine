"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { TrackSourceBadge } from "@/components/track-source-badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getCoreMemories, getObservabilityMemory, toCoreMemoryCard, toObservabilityMemoryCard } from "@/lib/product/data";
import { formatDateTime } from "@/lib/format";

import {
  ProductEmptyState,
  ProductErrorState,
  ProductLoadingState,
  ProductPageHeader,
} from "./primitives";

export function MemoryPage() {
  const coreMemoriesQuery = useQuery({
    queryKey: ["product", "memory", "core"],
    queryFn: () => getCoreMemories(20),
  });
  const observedMemoriesQuery = useQuery({
    queryKey: ["product", "memory", "observability"],
    queryFn: () => getObservabilityMemory(),
  });

  if (coreMemoriesQuery.isLoading || observedMemoriesQuery.isLoading) {
    return <ProductLoadingState label="Loading memory records" />;
  }

  const error = coreMemoriesQuery.error || observedMemoriesQuery.error;
  if (error instanceof Error) {
    return <ProductErrorState message={error.message} />;
  }

  const coreMemories = (coreMemoriesQuery.data?.items ?? []).map(toCoreMemoryCard);
  const observedMemories = (observedMemoriesQuery.data ?? []).map(toObservabilityMemoryCard);

  return (
    <div className="space-y-6 pb-8">
      <ProductPageHeader
        eyebrow="Memory"
        title="Understand what StateLock kept"
        copy="Memory stays split across Core durable memory and Observability learned memory so the architecture remains honest. Every card shows its source track."
      />

      <Tabs defaultValue="all">
        <TabsList>
          <TabsTrigger value="all">All memory</TabsTrigger>
          <TabsTrigger value="core">Core durable memory</TabsTrigger>
          <TabsTrigger value="observability">Observability learned memory</TabsTrigger>
        </TabsList>

        <TabsContent value="all">
          <MemoryGrid memories={[...observedMemories, ...coreMemories]} />
        </TabsContent>
        <TabsContent value="core">
          <MemoryGrid memories={coreMemories} />
        </TabsContent>
        <TabsContent value="observability">
          <MemoryGrid memories={observedMemories} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function MemoryGrid({
  memories,
}: {
  memories: Array<ReturnType<typeof toCoreMemoryCard> | ReturnType<typeof toObservabilityMemoryCard>>;
}) {
  if (!memories.length) {
    return (
      <ProductEmptyState
        title="No memory records yet"
        copy="As memories are stored in Core or learned in Observability, they will appear here with their source track."
      />
    );
  }

  return (
    <div className="grid gap-4 xl:grid-cols-2">
      {memories.map((memory) => (
        <Card key={`${memory.track}-${memory.id}`}>
          <CardHeader>
            <div className="flex items-center justify-between gap-3">
              <div>
                <CardTitle>{memory.title}</CardTitle>
                <CardDescription>
                  {memory.kind} · {memory.updatedAt ? formatDateTime(memory.updatedAt) : "No timestamp"}
                </CardDescription>
              </div>
              <TrackSourceBadge track={memory.track} />
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm leading-7 text-black/70">{memory.body}</p>
            <div className="space-y-2 text-sm text-black/60">
              {memory.whyItMatters.length ? (
                memory.whyItMatters.map((reason) => <p key={reason}>{reason}</p>)
              ) : (
                <p>The current API stores this memory, but does not expose a fuller rationale trail yet.</p>
              )}
            </div>
            <div className="flex flex-wrap gap-3 text-sm text-teal">
              <Link
                href={`/relationships?kind=memory&id=${memory.id}${memory.sourceConversationId ? `&conversationId=${memory.sourceConversationId}` : ""}`}
              >
                Inspect relationships
              </Link>
              {memory.tags.length ? <span>Tags: {memory.tags.join(", ")}</span> : null}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

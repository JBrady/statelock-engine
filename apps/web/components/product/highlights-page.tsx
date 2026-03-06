"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useEffect, useState } from "react";

import { TechnicalDetailsDrawer } from "@/components/technical-details-drawer";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getConversations, getConversationTurns, getHighlights, toHighlightVM } from "@/lib/product/data";

import {
  ProductEmptyState,
  ProductErrorState,
  ProductLoadingState,
  ProductPageHeader,
} from "./primitives";

export function HighlightsPage() {
  const conversationsQuery = useQuery({
    queryKey: ["product", "conversations"],
    queryFn: getConversations,
  });
  const [selectedConversationId, setSelectedConversationId] = useState("");
  const [selectedHighlightId, setSelectedHighlightId] = useState("");

  useEffect(() => {
    if (!selectedConversationId && conversationsQuery.data?.[0]) {
      setSelectedConversationId(conversationsQuery.data[0].conversation_id);
    }
  }, [conversationsQuery.data, selectedConversationId]);

  const highlightsQuery = useQuery({
    queryKey: ["product", "highlights", selectedConversationId],
    queryFn: () => getHighlights(selectedConversationId),
    enabled: Boolean(selectedConversationId),
  });
  const turnsQuery = useQuery({
    queryKey: ["product", "highlight-turns", selectedConversationId],
    queryFn: () => getConversationTurns(selectedConversationId),
    enabled: Boolean(selectedConversationId),
  });

  useEffect(() => {
    if (!selectedHighlightId && highlightsQuery.data?.[0]) {
      setSelectedHighlightId(highlightsQuery.data[0].span_id);
    }
  }, [highlightsQuery.data, selectedHighlightId]);

  if (conversationsQuery.isLoading) {
    return <ProductLoadingState label="Loading highlights" />;
  }

  if (conversationsQuery.error instanceof Error) {
    return <ProductErrorState message={conversationsQuery.error.message} />;
  }

  const conversations = conversationsQuery.data ?? [];
  const highlights = (highlightsQuery.data ?? []).map(toHighlightVM);
  const selectedHighlight = highlights.find((item) => item.id === selectedHighlightId);
  const turnsById = new Map((turnsQuery.data ?? []).map((turn) => [turn.turn_id, turn]));

  return (
    <div className="space-y-6 pb-8">
      <ProductPageHeader
        eyebrow="Highlights"
        title="What StateLock Noticed"
        copy="Highlights are the pieces of a conversation that StateLock pulled forward as potentially meaningful. The UI keeps the language humane while preserving access to the raw details when needed."
        actions={
          conversations.length ? (
            <select
              className="rounded-full border border-black/10 bg-white/80 px-4 py-2 text-sm"
              onChange={(event) => {
                setSelectedConversationId(event.target.value);
                setSelectedHighlightId("");
              }}
              value={selectedConversationId}
            >
              {conversations.map((conversation) => (
                <option key={conversation.conversation_id} value={conversation.conversation_id}>
                  {conversation.title}
                </option>
              ))}
            </select>
          ) : null
        }
      />

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Highlights</CardTitle>
            <CardDescription>Select a highlight to inspect its evidence and relationships.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {highlights.length ? (
              highlights.map((highlight) => (
                <button
                  className={`w-full rounded-3xl border p-4 text-left transition ${
                    highlight.id === selectedHighlightId
                      ? "border-moss bg-moss/10"
                      : "border-black/10 bg-white/80"
                  }`}
                  key={highlight.id}
                  onClick={() => setSelectedHighlightId(highlight.id)}
                  type="button"
                >
                  <div className="flex items-center justify-between gap-3">
                    <h3 className="font-display text-lg text-ink">{highlight.label}</h3>
                    {typeof highlight.trust === "number" ? (
                      <Badge className="border-moss/20 bg-moss/10 text-moss">
                        Trust {highlight.trust.toFixed(2)}
                      </Badge>
                    ) : null}
                  </div>
                  <p className="mt-2 line-clamp-3 text-sm leading-6 text-black/65">
                    {highlight.text}
                  </p>
                </button>
              ))
            ) : (
              <ProductEmptyState
                title="No highlights yet"
                copy="Segmentation or extraction has not surfaced highlight records for this conversation."
              />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{selectedHighlight?.label ?? "Highlight detail"}</CardTitle>
            <CardDescription>
              Relationship and provenance details are derived from the current span payloads.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            {selectedHighlight ? (
              <>
                <div className="rounded-3xl border border-black/10 bg-white/80 p-5">
                  <p className="text-sm leading-7 text-black/72">{selectedHighlight.text}</p>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="rounded-3xl border border-black/10 bg-white/80 p-4">
                    <p className="text-sm uppercase tracking-[0.14em] text-black/50">Evidence</p>
                    <div className="mt-3 space-y-2 text-sm text-black/65">
                      {selectedHighlight.sourceMessageIds.length ? (
                        selectedHighlight.sourceMessageIds.map((messageId) => (
                          <div key={messageId}>
                            <p className="font-medium text-black/70">Message {messageId.slice(0, 8)}</p>
                            <p>
                              {turnsById.get(messageId)?.text ?? "The backing message text is not currently available."}
                            </p>
                          </div>
                        ))
                      ) : (
                        <p>No source message references are currently exposed.</p>
                      )}
                    </div>
                  </div>
                  <div className="rounded-3xl border border-black/10 bg-white/80 p-4">
                    <p className="text-sm uppercase tracking-[0.14em] text-black/50">Connections</p>
                    <div className="mt-3 space-y-2 text-sm text-black/65">
                      {selectedHighlight.links.length ? (
                        selectedHighlight.links.map((link) => (
                          <p key={`${link.kind}-${link.targetId}`}>
                            {link.label}: {link.targetId}
                          </p>
                        ))
                      ) : (
                        <p>No visible connection records yet.</p>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex flex-wrap gap-3">
                  <Link
                    className="text-sm text-teal"
                    href={`/relationships?kind=highlight&id=${selectedHighlight.id}&conversationId=${selectedConversationId}`}
                  >
                    Inspect relationships
                  </Link>
                  <TechnicalDetailsDrawer title="Highlight technical details">
                    <pre className="text-xs leading-6 text-black/75">
                      {JSON.stringify(selectedHighlight, null, 2)}
                    </pre>
                  </TechnicalDetailsDrawer>
                </div>
              </>
            ) : (
              <ProductEmptyState
                title="Pick a highlight"
                copy="Select a highlight to see where it came from and how it connects."
              />
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

"use client";

import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { TechnicalDetailsDrawer } from "@/components/technical-details-drawer";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  getConversationThreads,
  getConversationTurns,
  getConversations,
  getLatestWorkingContext,
  toActiveContextVM,
  toMessageVM,
} from "@/lib/product/data";
import { formatDateTime } from "@/lib/format";

import {
  ProductEmptyState,
  ProductErrorState,
  ProductLoadingState,
  ProductPageHeader,
} from "./primitives";

export function ConversationsPage() {
  const conversationsQuery = useQuery({
    queryKey: ["product", "conversations"],
    queryFn: getConversations,
  });
  const [selectedConversationId, setSelectedConversationId] = useState("");

  useEffect(() => {
    if (!selectedConversationId && conversationsQuery.data?.[0]) {
      setSelectedConversationId(conversationsQuery.data[0].conversation_id);
    }
  }, [conversationsQuery.data, selectedConversationId]);

  const turnsQuery = useQuery({
    queryKey: ["product", "conversation-turns", selectedConversationId],
    queryFn: () => getConversationTurns(selectedConversationId),
    enabled: Boolean(selectedConversationId),
  });
  const threadsQuery = useQuery({
    queryKey: ["product", "conversation-threads", selectedConversationId],
    queryFn: () => getConversationThreads(selectedConversationId),
    enabled: Boolean(selectedConversationId),
  });
  const contextQuery = useQuery({
    queryKey: ["product", "conversation-context", selectedConversationId],
    queryFn: () => getLatestWorkingContext(selectedConversationId),
    enabled: Boolean(selectedConversationId),
  });

  if (conversationsQuery.isLoading) {
    return <ProductLoadingState label="Loading conversations" />;
  }

  if (conversationsQuery.error instanceof Error) {
    return <ProductErrorState message={conversationsQuery.error.message} />;
  }

  const conversations = conversationsQuery.data ?? [];
  const selectedConversation = conversations.find(
    (conversation) => conversation.conversation_id === selectedConversationId,
  );
  const messages = (turnsQuery.data ?? []).map(toMessageVM);
  const activeContext = toActiveContextVM(contextQuery.data ?? null);

  return (
    <div className="space-y-6 pb-8">
      <ProductPageHeader
        eyebrow="Conversations"
        title="See what happened, in order"
        copy="Conversations anchor the rest of the product. Messages, topic threads, and the active context all stay tied to the same conversation boundary."
      />

      {!conversations.length ? (
        <ProductEmptyState
          title="No conversations yet"
          copy="Start with the Observability seed flow to populate this view."
        />
      ) : (
        <div className="grid gap-6 xl:grid-cols-[0.8fr_1.2fr]">
          <Card>
            <CardHeader>
              <CardTitle>Conversations</CardTitle>
              <CardDescription>Select a conversation to inspect its messages and focus areas.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {conversations.map((conversation) => (
                <button
                  className={`w-full rounded-3xl border p-4 text-left transition ${
                    conversation.conversation_id === selectedConversationId
                      ? "border-moss bg-moss/10"
                      : "border-black/10 bg-white/80"
                  }`}
                  key={conversation.conversation_id}
                  onClick={() => setSelectedConversationId(conversation.conversation_id)}
                  type="button"
                >
                  <h3 className="font-display text-lg text-ink">{conversation.title}</h3>
                  <p className="mt-2 text-sm text-black/60">
                    Updated {formatDateTime(conversation.updated_at)}
                  </p>
                </button>
              ))}
            </CardContent>
          </Card>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>{selectedConversation?.title ?? "Conversation detail"}</CardTitle>
                <CardDescription>
                  Messages are shown in conversation order using the real turn stream.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {messages.length ? (
                  messages.map((message, index) => (
                    <div key={message.id} className="rounded-3xl border border-black/10 bg-white/80 p-4">
                      <div className="flex items-center justify-between gap-3">
                        <span className="text-sm uppercase tracking-[0.16em] text-black/50">
                          {message.role}
                        </span>
                        <span className="text-sm text-black/50">
                          Message {index + 1} · {formatDateTime(message.createdAt)}
                        </span>
                      </div>
                      <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-black/72">
                        {message.text}
                      </p>
                    </div>
                  ))
                ) : (
                  <ProductEmptyState
                    title="No messages returned"
                    copy="This conversation exists, but no message turns are currently visible."
                  />
                )}
              </CardContent>
            </Card>

            <div className="grid gap-6 lg:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Topic threads</CardTitle>
                  <CardDescription>
                    These threads come from the current segmentation model, not a synthetic UI grouping.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {(threadsQuery.data ?? []).length ? (
                    (threadsQuery.data ?? []).map((thread) => (
                      <div key={thread.thread_id} className="rounded-3xl border border-black/10 bg-white/80 p-4">
                        <h3 className="font-display text-lg">{thread.name}</h3>
                        <p className="mt-2 text-sm text-black/60">{thread.summary}</p>
                        <p className="mt-3 text-xs uppercase tracking-[0.14em] text-black/45">
                          {thread.span_count} highlights · active {formatDateTime(thread.last_activity_at)}
                        </p>
                      </div>
                    ))
                  ) : (
                    <ProductEmptyState
                      title="No topic threads yet"
                      copy="Segmentation has not produced visible topic groupings for this conversation."
                    />
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Active Context</CardTitle>
                  <CardDescription>
                    This is the current working context assembled for the conversation.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {activeContext ? (
                    <>
                      <p className="rounded-3xl border border-black/10 bg-white/80 p-4 text-sm leading-7 text-black/72">
                        {activeContext.assembledText}
                      </p>
                      <div className="text-sm text-black/60">
                        {activeContext.selectedHighlightIds.length} highlight(s) selected · built{" "}
                        {formatDateTime(activeContext.createdAt)}
                      </div>
                    </>
                  ) : (
                    <ProductEmptyState
                      title="No active context yet"
                      copy="StateLock has not built a working context for this conversation yet."
                    />
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      )}

      <div className="flex justify-end">
        <TechnicalDetailsDrawer title="Conversation technical details">
          <pre className="text-xs leading-6 text-black/75">
            {JSON.stringify(
              {
                selectedConversation,
                turns: turnsQuery.data,
                threads: threadsQuery.data,
                workingContext: contextQuery.data,
              },
              null,
              2,
            )}
          </pre>
        </TechnicalDetailsDrawer>
      </div>
    </div>
  );
}

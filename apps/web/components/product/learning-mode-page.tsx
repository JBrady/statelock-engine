"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  getConversations,
  toLearningModeVM,
  updateConversationSettings,
} from "@/lib/product/data";

import {
  ProductEmptyState,
  ProductErrorState,
  ProductLoadingState,
  ProductPageHeader,
} from "./primitives";

export function LearningModePage() {
  const queryClient = useQueryClient();
  const conversationsQuery = useQuery({
    queryKey: ["product", "conversations"],
    queryFn: getConversations,
  });
  const [selectedConversationId, setSelectedConversationId] = useState("");
  const [formValues, setFormValues] = useState({
    max_context_tokens: 6000,
    telemetry_mode: "standard",
    target_thread_mode: "auto",
    pinned_thread_id: "",
  });

  useEffect(() => {
    if (!selectedConversationId && conversationsQuery.data?.[0]) {
      setSelectedConversationId(conversationsQuery.data[0].conversation_id);
    }
  }, [conversationsQuery.data, selectedConversationId]);

  const conversation = (conversationsQuery.data ?? []).find(
    (item) => item.conversation_id === selectedConversationId,
  );

  useEffect(() => {
    if (!conversation) {
      return;
    }
    setFormValues({
      max_context_tokens: conversation.settings.max_context_tokens,
      telemetry_mode: conversation.settings.telemetry_mode,
      target_thread_mode: conversation.settings.target_thread_mode,
      pinned_thread_id: conversation.settings.pinned_thread_id ?? "",
    });
  }, [conversation]);

  const mutation = useMutation({
    mutationFn: async () => {
      if (!conversation) {
        throw new Error("No conversation selected");
      }
      return updateConversationSettings(conversation, {
        ...formValues,
        pinned_thread_id: formValues.pinned_thread_id || null,
      });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["product", "conversations"] });
    },
  });

  if (conversationsQuery.isLoading) {
    return <ProductLoadingState label="Loading learning mode" />;
  }

  if (conversationsQuery.error instanceof Error) {
    return <ProductErrorState message={conversationsQuery.error.message} />;
  }

  if (!conversation) {
    return (
      <ProductEmptyState
        title="No conversation selected"
        copy="Learning Mode is conversation-scoped because those are the stable settings the backend already supports."
      />
    );
  }

  const learningMode = toLearningModeVM(conversation);

  return (
    <div className="space-y-6 pb-8">
      <ProductPageHeader
        eyebrow="Learning Mode"
        title="Tune the current learning posture"
        copy="This page stays read-mostly and only edits stable conversation settings that already exist in Observability today."
        actions={
          <select
            className="rounded-full border border-black/10 bg-white/80 px-4 py-2 text-sm"
            onChange={(event) => setSelectedConversationId(event.target.value)}
            value={selectedConversationId}
          >
            {(conversationsQuery.data ?? []).map((item) => (
              <option key={item.conversation_id} value={item.conversation_id}>
                {item.title}
              </option>
            ))}
          </select>
        }
      />

      <div className="grid gap-6 xl:grid-cols-[1fr_0.8fr]">
        <Card>
          <CardHeader>
              <CardTitle>Current settings</CardTitle>
              <CardDescription>
              These controls reflect stable settings StateLock already uses today.
              </CardDescription>
            </CardHeader>
          <CardContent className="space-y-5">
            <div className="grid gap-4">
              {learningMode.fields.map((field) => (
                <div key={field.key} className="rounded-3xl border border-black/10 bg-white/80 p-4">
                  <label className="font-display text-lg text-ink" htmlFor={field.key}>
                    {field.label}
                  </label>
                  <p className="mt-2 text-sm leading-6 text-black/60">{field.helperText}</p>
                  <div className="mt-4">
                    {field.key === "activeContextSize" ? (
                      <input
                        className="w-full rounded-2xl border border-black/10 bg-white px-4 py-3 text-sm"
                        id={field.key}
                        min={1000}
                        onChange={(event) =>
                          setFormValues((current) => ({
                            ...current,
                            max_context_tokens: Number(event.target.value),
                          }))
                        }
                        type="number"
                        value={formValues.max_context_tokens}
                      />
                    ) : field.key === "learningDepth" ? (
                      <select
                        className="w-full rounded-2xl border border-black/10 bg-white px-4 py-3 text-sm"
                        id={field.key}
                        onChange={(event) =>
                          setFormValues((current) => ({
                            ...current,
                            telemetry_mode: event.target.value,
                          }))
                        }
                        value={formValues.telemetry_mode}
                      >
                        <option value="off">Off</option>
                        <option value="minimal">Minimal</option>
                        <option value="standard">Standard</option>
                        <option value="verbose">Verbose</option>
                      </select>
                    ) : field.key === "focusStrategy" ? (
                      <select
                        className="w-full rounded-2xl border border-black/10 bg-white px-4 py-3 text-sm"
                        id={field.key}
                        onChange={(event) =>
                          setFormValues((current) => ({
                            ...current,
                            target_thread_mode: event.target.value,
                          }))
                        }
                        value={formValues.target_thread_mode}
                      >
                        <option value="auto">Auto</option>
                        <option value="pinned">Pinned</option>
                      </select>
                    ) : (
                      <input
                        className="w-full rounded-2xl border border-black/10 bg-white px-4 py-3 text-sm"
                        id={field.key}
                        onChange={(event) =>
                          setFormValues((current) => ({
                            ...current,
                            pinned_thread_id: event.target.value,
                          }))
                        }
                        type="text"
                        value={formValues.pinned_thread_id}
                      />
                    )}
                  </div>
                </div>
              ))}
            </div>
            <div className="flex items-center gap-3">
              <Button onClick={() => mutation.mutate()}>
                Save current settings
              </Button>
              {mutation.isPending ? <span className="text-sm text-black/60">Saving…</span> : null}
              {mutation.isSuccess ? <span className="text-sm text-moss">Saved</span> : null}
              {mutation.error instanceof Error ? (
                <span className="text-sm text-rust">{mutation.error.message}</span>
              ) : null}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Current behavior and limits</CardTitle>
            <CardDescription>
              These notes explain what the current backend supports and what remains future-facing.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm leading-7 text-black/65">
            {learningMode.informationalNotes.map((note) => (
              <p key={note}>{note}</p>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

import { RelationshipsPage } from "@/components/product/relationships-page";

export default async function Page({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const kind = typeof params.kind === "string" ? params.kind : undefined;
  const id = typeof params.id === "string" ? params.id : undefined;
  const conversationId =
    typeof params.conversationId === "string" ? params.conversationId : undefined;

  return (
    <RelationshipsPage
      initialConversationId={conversationId}
      initialId={id}
      initialKind={
        kind === "memory" || kind === "highlight" || kind === "conversation"
          ? kind
          : undefined
      }
    />
  );
}

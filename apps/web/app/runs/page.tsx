import { RunsPage } from "@/components/product/runs-page";

export default async function Page({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const conversationId =
    typeof params.conversationId === "string" ? params.conversationId : undefined;
  const runGroupId =
    typeof params.runGroupId === "string" ? params.runGroupId : undefined;

  return (
    <RunsPage
      initialConversationId={conversationId}
      initialRunGroupId={runGroupId}
    />
  );
}

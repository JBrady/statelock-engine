"use client";

import { useEffect, useState } from "react";

import { JsonBlock } from "@/components/json-block";
import { LoadState } from "@/components/load-state";
import { PageHeader } from "@/components/page-header";
import { requestPayload } from "@/lib/client";

type TagsResponse = {
  items: Array<{ tag: string; count: number }>;
  total: number;
  limit: number;
  offset: number;
};

export default function CoreTagsPage() {
  const [tags, setTags] = useState<TagsResponse["items"]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    async function loadTags() {
      setLoading(true);
      setError(null);
      try {
        const response = await requestPayload<TagsResponse>(
          "/api/core/tags?limit=50&offset=0",
        );
        if (mounted) {
          setTags(response.data.items);
        }
      } catch (loadError) {
        if (mounted) {
          setError(loadError instanceof Error ? loadError.message : "Failed to load tags.");
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    void loadTags();

    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="stack">
      <PageHeader
        title="Core Tags"
        copy="Read the current tag catalog exactly as exposed by the Insights endpoint, with no extra grouping or inferred search semantics."
      />

      <LoadState
        loading={loading}
        error={error}
        empty={!loading && !tags.length ? "No tags returned yet." : null}
      />

      {tags.length ? (
        <section className="table-wrap">
          <h2>Current tag counts</h2>
          <table>
            <thead>
              <tr>
                <th>Tag</th>
                <th>Count</th>
              </tr>
            </thead>
            <tbody>
              {tags.map((tag) => (
                <tr key={tag.tag}>
                  <td>
                    <span className="pill">{tag.tag}</span>
                  </td>
                  <td>{tag.count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ) : null}

      <JsonBlock title="Tag payload" value={{ items: tags }} />
    </div>
  );
}

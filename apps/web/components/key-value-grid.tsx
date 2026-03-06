import { scalarEntries } from "@/lib/format";

type KeyValueGridProps = {
  record: Record<string, unknown>;
};

export function KeyValueGrid({ record }: KeyValueGridProps) {
  const rows = scalarEntries(record);

  if (!rows.length) {
    return <div className="empty">No scalar fields returned for this object.</div>;
  }

  return (
    <div className="key-grid">
      {rows.map(([key, value]) => (
        <div className="key-box" key={key}>
          <strong>{key}</strong>
          <div className="muted">{value}</div>
        </div>
      ))}
    </div>
  );
}

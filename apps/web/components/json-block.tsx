import { formatMaybeJson } from "@/lib/format";

type JsonBlockProps = {
  title?: string;
  value: unknown;
};

export function JsonBlock({ title, value }: JsonBlockProps) {
  return (
    <section className="panel">
      {title ? <h3>{title}</h3> : null}
      <div className="json-block">
        <pre>{formatMaybeJson(value)}</pre>
      </div>
    </section>
  );
}

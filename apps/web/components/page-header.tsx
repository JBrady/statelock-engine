import type { ReactNode } from "react";

type PageHeaderProps = {
  title: string;
  copy: string;
  actions?: ReactNode;
};

export function PageHeader({ title, copy, actions }: PageHeaderProps) {
  return (
    <div className="page-header">
      <div>
        <h1 className="page-title">{title}</h1>
        <p className="page-copy">{copy}</p>
      </div>
      {actions ? <div className="toolbar">{actions}</div> : null}
    </div>
  );
}

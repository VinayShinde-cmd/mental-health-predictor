import type { ReactNode } from "react";
import { Button } from "./Button.tsx";

/** Placeholder block shown while data loads. Decorative: hidden from assistive technology. */
export function Skeleton({ height = "2.75rem", width = "100%" }: { height?: string; width?: string }) {
  return <div className="skeleton" aria-hidden="true" style={{ height, width }} />;
}

interface EmptyStateProps {
  title: string;
  children: ReactNode;
  action?: { label: string; onClick: () => void };
}

/** Nothing to show yet: say why, and what to do next. */
export function EmptyState({ title, children, action }: EmptyStateProps) {
  return (
    <div className="state">
      <h3 className="state__title">{title}</h3>
      <p className="state__body">{children}</p>
      {action ? (
        <Button variant="secondary" onClick={action.onClick}>
          {action.label}
        </Button>
      ) : null}
    </div>
  );
}

interface ErrorStateProps {
  title: string;
  message: string;
  onRetry?: () => void;
  retryLabel?: string;
}

/** Something failed: say what happened and offer a way forward. */
export function ErrorState({ title, message, onRetry, retryLabel = "Try again" }: ErrorStateProps) {
  return (
    <div className="state state--error" role="alert">
      <h3 className="state__title">{title}</h3>
      <p className="state__body">{message}</p>
      {onRetry ? (
        <Button variant="secondary" onClick={onRetry}>
          {retryLabel}
        </Button>
      ) : null}
    </div>
  );
}

/** Inline message inside a form. `tone="warning"` is for things to know, `error` for things to fix. */
export function Alert({ tone, children }: { tone: "error" | "warning"; children: ReactNode }) {
  return (
    <div className={`alert alert--${tone}`} role={tone === "error" ? "alert" : "note"}>
      {children}
    </div>
  );
}

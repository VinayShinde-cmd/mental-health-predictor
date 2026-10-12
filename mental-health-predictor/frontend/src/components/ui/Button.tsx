import type { ButtonHTMLAttributes } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "quiet";
  /** Shows progress, keeps the label readable, and blocks repeat clicks. */
  loading?: boolean;
}

export function Button({ variant = "primary", loading = false, disabled, className, children, ...rest }: ButtonProps) {
  const classes = ["button", `button--${variant}`, className].filter(Boolean).join(" ");
  return (
    <button type="button" {...rest} className={classes} disabled={disabled || loading} aria-busy={loading || undefined}>
      {children}
    </button>
  );
}

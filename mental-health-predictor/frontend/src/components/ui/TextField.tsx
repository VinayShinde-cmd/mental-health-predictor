import type { ChangeEvent, FocusEvent } from "react";

interface TextFieldProps {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  onBlur?: (event: FocusEvent<HTMLInputElement>) => void;
  /** Helper text shown under the field, e.g. the range the model has seen. */
  hint?: string;
  error?: string;
  /** Unit shown after the value, e.g. "hours a day". Read aloud as part of the hint. */
  unit?: string;
  inputMode?: "numeric" | "decimal" | "text";
  disabled?: boolean;
}

/** Text input for numbers. Uses text + inputMode so mobile keyboards are right and our own messages show. */
export function TextField({
  id,
  label,
  value,
  onChange,
  onBlur,
  hint,
  error,
  unit,
  inputMode = "decimal",
  disabled,
}: TextFieldProps) {
  const hintId = `${id}-hint`;
  const errorId = `${id}-error`;
  const describedBy = [hint || unit ? hintId : null, error ? errorId : null].filter(Boolean).join(" ");
  const hintText = [unit, hint].filter(Boolean).join(". ");

  return (
    <div className="field">
      <label className="field__label" htmlFor={id}>
        {label}
      </label>
      <input
        id={id}
        className="field__control"
        type="text"
        inputMode={inputMode}
        autoComplete="off"
        value={value}
        disabled={disabled}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy || undefined}
        onChange={(event: ChangeEvent<HTMLInputElement>) => onChange(event.target.value)}
        onBlur={onBlur}
      />
      {hintText ? (
        <p className="field__hint" id={hintId}>
          {hintText}
        </p>
      ) : null}
      {error ? (
        <p className="field__error" id={errorId}>
          {error}
        </p>
      ) : null}
    </div>
  );
}

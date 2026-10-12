import type { FormEvent } from "react";
import { useEffect, useState } from "react";
import type { FieldIssue, FieldName, NumericField, Options, PredictRequest } from "../api/types.ts";
import { countryLabel, FIELD_LABELS, FIELD_UNITS } from "../lib/format.ts";
import {
  EMPTY_VALUES,
  firstInvalidField,
  issuesToErrors,
  toRequest,
  validateField,
  validateForm,
} from "../lib/validation.ts";
import type { FormErrors, FormValues } from "../lib/validation.ts";
import { Button } from "./ui/Button.tsx";
import { Alert } from "./ui/Feedback.tsx";
import { SelectField } from "./ui/SelectField.tsx";
import { TextField } from "./ui/TextField.tsx";

interface PredictionFormProps {
  options: Options;
  pending: boolean;
  /** Field-level problems the server reported (shown next to the matching field). */
  serverIssues: FieldIssue[];
  /** Form-level message, e.g. "Some answers need a look." */
  formMessage?: string;
  onSubmit: (payload: PredictRequest) => void;
  onClear: () => void;
}

const WHOLE_NUMBER_FIELDS: FieldName[] = ["age", "daily_unlocks"];
const asOptions = (values: string[]) => values.map((value) => ({ value, label: value }));

export function PredictionForm({ options, pending, serverIssues, formMessage, onSubmit, onClear }: PredictionFormProps) {
  const [values, setValues] = useState<FormValues>(EMPTY_VALUES);
  const [errors, setErrors] = useState<FormErrors>({});
  const [serverErrors, setServerErrors] = useState<FormErrors>({});

  useEffect(() => {
    setServerErrors(issuesToErrors(serverIssues));
  }, [serverIssues]);

  const errorFor = (name: FieldName) => errors[name] ?? serverErrors[name];

  function change(name: FieldName, value: string) {
    setValues((current) => ({ ...current, [name]: value }));
    // Editing a field clears its message; it is re-checked when the field loses focus or on submit.
    setErrors((current) => ({ ...current, [name]: undefined }));
    setServerErrors((current) => ({ ...current, [name]: undefined }));
  }

  function check(name: FieldName) {
    setErrors((current) => ({ ...current, [name]: validateField(name, values[name], options) }));
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const found = validateForm(values, options);
    setErrors(found);
    const first = firstInvalidField(found);
    if (first) {
      document.getElementById(`field-${first}`)?.focus();
      return;
    }
    onSubmit(toRequest(values));
  }

  function handleClear() {
    setValues(EMPTY_VALUES);
    setErrors({});
    setServerErrors({});
    onClear();
  }

  const number = (name: NumericField) => {
    const trained = options.training_ranges[name];
    return (
      <TextField
        id={`field-${name}`}
        label={FIELD_LABELS[name]}
        value={values[name]}
        unit={FIELD_UNITS[name]}
        hint={`Survey range ${trained.min} to ${trained.max}`}
        inputMode={WHOLE_NUMBER_FIELDS.includes(name) ? "numeric" : "decimal"}
        error={errorFor(name)}
        disabled={pending}
        onChange={(value) => change(name, value)}
        onBlur={() => check(name)}
      />
    );
  };

  const choice = (name: FieldName, list: { value: string; label: string }[]) => (
    <SelectField
      id={`field-${name}`}
      label={FIELD_LABELS[name]}
      value={values[name]}
      options={list}
      error={errorFor(name)}
      disabled={pending}
      onChange={(value) => change(name, value)}
      onBlur={() => check(name)}
    />
  );

  return (
    <form className="form" onSubmit={handleSubmit} noValidate>
      <fieldset className="group" disabled={pending}>
        <legend className="group__title">About you</legend>
        <div className="fields">
          {number("age")}
          {choice("gender", asOptions(options.genders))}
          {choice("academic_level", asOptions(options.academic_levels))}
          {choice(
            "country",
            options.countries.map((value) => ({ value, label: countryLabel(value) })),
          )}
        </div>
      </fieldset>

      <fieldset className="group" disabled={pending}>
        <legend className="group__title">Your phone</legend>
        <div className="fields">
          {choice("most_used_platform", asOptions(options.platforms))}
          {choice("purpose_of_use", asOptions(options.purposes))}
          {number("avg_daily_usage_hours")}
          {number("daily_unlocks")}
        </div>
      </fieldset>

      <fieldset className="group" disabled={pending}>
        <legend className="group__title">Your day</legend>
        <div className="fields">
          {number("study_hours")}
          {number("physical_activity_hours")}
          {number("sleep_hours_per_night")}
          {choice("stress_level", asOptions(options.stress_levels))}
        </div>
      </fieldset>

      {formMessage ? <Alert tone="error">{formMessage}</Alert> : null}

      <div className="form__actions">
        <Button type="submit" loading={pending}>
          {pending ? "Estimating…" : "Estimate my score"}
        </Button>
        <Button variant="quiet" onClick={handleClear} disabled={pending}>
          Clear answers
        </Button>
      </div>
    </form>
  );
}

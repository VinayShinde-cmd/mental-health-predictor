import type { FieldName, NumericField, Options, PredictRequest } from "../api/types.ts";
import { CATEGORICAL_FIELDS, NUMERIC_FIELDS } from "../api/types.ts";

/** Form state holds raw text, so half-typed input never fights the user. */
export type FormValues = Record<FieldName, string>;
export type FormErrors = Partial<Record<FieldName, string>>;

/** Order the fields appear in the form; also the order focus moves to the first problem. */
export const FIELD_ORDER: FieldName[] = [
  "age",
  "gender",
  "academic_level",
  "country",
  "most_used_platform",
  "purpose_of_use",
  "avg_daily_usage_hours",
  "daily_unlocks",
  "study_hours",
  "physical_activity_hours",
  "sleep_hours_per_night",
  "stress_level",
];

const WHOLE_NUMBER_FIELDS = new Set<FieldName>(["age", "daily_unlocks"]);

export const EMPTY_VALUES: FormValues = {
  age: "",
  gender: "",
  country: "",
  academic_level: "",
  most_used_platform: "",
  purpose_of_use: "",
  avg_daily_usage_hours: "",
  daily_unlocks: "",
  study_hours: "",
  physical_activity_hours: "",
  sleep_hours_per_night: "",
  stress_level: "",
};

function isNumericField(name: FieldName): name is NumericField {
  return (NUMERIC_FIELDS as readonly string[]).includes(name);
}

/** "6,5" and "6.5" both mean 6.5. An empty string must not turn into 0. */
export function parseNumber(raw: string): number {
  const text = raw.trim().replace(",", ".");
  return text === "" ? Number.NaN : Number(text);
}

function optionsFor(name: FieldName, options: Options): string[] {
  switch (name) {
    case "gender":
      return options.genders;
    case "country":
      return options.countries;
    case "academic_level":
      return options.academic_levels;
    case "most_used_platform":
      return options.platforms;
    case "purpose_of_use":
      return options.purposes;
    case "stress_level":
      return options.stress_levels;
    default:
      return [];
  }
}

/** Same rules the server enforces (limits come from /api/options). The server stays the source of truth. */
export function validateField(name: FieldName, raw: string, options: Options): string | undefined {
  if (isNumericField(name)) {
    const value = parseNumber(raw);
    if (!Number.isFinite(value)) return "Enter a number.";
    if (WHOLE_NUMBER_FIELDS.has(name) && !Number.isInteger(value)) return "Enter a whole number.";
    const { min, max } = options.limits[name];
    if (value < min || value > max) return `Enter a value between ${min} and ${max}.`;
    return undefined;
  }
  if (raw === "") return "Choose an option.";
  if (!optionsFor(name, options).includes(raw)) return "Choose one of the listed options.";
  return undefined;
}

export function validateForm(values: FormValues, options: Options): FormErrors {
  const errors: FormErrors = {};
  for (const name of [...NUMERIC_FIELDS, ...CATEGORICAL_FIELDS]) {
    const message = validateField(name, values[name], options);
    if (message) errors[name] = message;
  }
  return errors;
}

export function firstInvalidField(errors: FormErrors): FieldName | undefined {
  return FIELD_ORDER.find((name) => errors[name] !== undefined);
}

/** Only call after validateForm returned no errors. */
export function toRequest(values: FormValues): PredictRequest {
  return {
    age: parseNumber(values.age),
    gender: values.gender,
    country: values.country,
    academic_level: values.academic_level,
    most_used_platform: values.most_used_platform,
    purpose_of_use: values.purpose_of_use,
    avg_daily_usage_hours: parseNumber(values.avg_daily_usage_hours),
    daily_unlocks: parseNumber(values.daily_unlocks),
    study_hours: parseNumber(values.study_hours),
    physical_activity_hours: parseNumber(values.physical_activity_hours),
    sleep_hours_per_night: parseNumber(values.sleep_hours_per_night),
    stress_level: values.stress_level,
  };
}

/** Turn the server's field issues into form errors. Unknown field names are ignored. */
export function issuesToErrors(issues: { field: string; message: string }[]): FormErrors {
  const errors: FormErrors = {};
  for (const issue of issues) {
    if ((FIELD_ORDER as string[]).includes(issue.field)) {
      errors[issue.field as FieldName] ??= issue.message;
    }
  }
  return errors;
}

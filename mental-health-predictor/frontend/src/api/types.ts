export const NUMERIC_FIELDS = [
  "age",
  "avg_daily_usage_hours",
  "daily_unlocks",
  "study_hours",
  "physical_activity_hours",
  "sleep_hours_per_night",
] as const;

export const CATEGORICAL_FIELDS = [
  "gender",
  "country",
  "academic_level",
  "most_used_platform",
  "purpose_of_use",
  "stress_level",
] as const;

export type NumericField = (typeof NUMERIC_FIELDS)[number];
export type CategoricalField = (typeof CATEGORICAL_FIELDS)[number];
export type FieldName = NumericField | CategoricalField;

export interface Range {
  min: number;
  max: number;
}

/** GET /api/options */
export interface Options {
  genders: string[];
  academic_levels: string[];
  platforms: string[];
  purposes: string[];
  countries: string[];
  stress_levels: string[];
  limits: Record<NumericField, Range>;
  training_ranges: Record<NumericField, Range>;
}

/** POST /api/predict body. Field names match the form keys. */
export interface PredictRequest {
  age: number;
  gender: string;
  country: string;
  academic_level: string;
  most_used_platform: string;
  purpose_of_use: string;
  avg_daily_usage_hours: number;
  daily_unlocks: number;
  study_hours: number;
  physical_activity_hours: number;
  sleep_hours_per_night: number;
  stress_level: string;
}

export type Band = "below_typical" | "typical" | "above_typical";

/** POST /api/predict response. */
export interface Prediction {
  score: number;
  band: Band;
  band_label: string;
  typical_range: Range;
  scale: Range;
  warnings: string[];
  disclaimer: string;
  model_id: string;
}

export interface FieldIssue {
  field: string;
  message: string;
}

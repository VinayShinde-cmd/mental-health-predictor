import type { Range } from "../api/types.ts";

export function formatScore(score: number): string {
  return score.toFixed(1);
}

/** Position of a value along a scale as a percentage, clamped to the scale's ends. */
export function percentAlong(value: number, scale: Range): number {
  const span = scale.max - scale.min;
  if (span <= 0) return 0;
  return Math.min(100, Math.max(0, ((value - scale.min) / span) * 100));
}

/** Whole-number tick marks that fall inside the scale. */
export function wholeTicks(scale: Range): number[] {
  const ticks: number[] = [];
  for (let n = Math.ceil(scale.min); n <= Math.floor(scale.max); n += 1) ticks.push(n);
  return ticks;
}

export function countryLabel(country: string): string {
  return country === "Other" ? "Another country" : country;
}

export const FIELD_LABELS = {
  age: "Age",
  gender: "Gender",
  country: "Country",
  academic_level: "Academic level",
  most_used_platform: "Most-used platform",
  purpose_of_use: "Main reason you use it",
  avg_daily_usage_hours: "Daily phone use",
  daily_unlocks: "Phone unlocks per day",
  study_hours: "Study time",
  physical_activity_hours: "Physical activity",
  sleep_hours_per_night: "Sleep",
  stress_level: "Stress level",
} as const;

export const FIELD_UNITS: Partial<Record<keyof typeof FIELD_LABELS, string>> = {
  age: "years",
  avg_daily_usage_hours: "hours a day",
  daily_unlocks: "times a day",
  study_hours: "hours a day",
  physical_activity_hours: "hours a day",
  sleep_hours_per_night: "hours a night",
};

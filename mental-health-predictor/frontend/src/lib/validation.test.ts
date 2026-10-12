import { describe, expect, it } from "vitest";
import type { Options } from "../api/types.ts";
import {
  EMPTY_VALUES,
  firstInvalidField,
  issuesToErrors,
  parseNumber,
  toRequest,
  validateField,
  validateForm,
} from "./validation.ts";
import type { FormValues } from "./validation.ts";

const limit = (min: number, max: number) => ({ min, max });
const OPTIONS: Options = {
  genders: ["Female", "Male"],
  academic_levels: ["Graduate", "High School", "Undergraduate"],
  platforms: ["Instagram", "TikTok"],
  purposes: ["Education", "Entertainment"],
  countries: ["India", "Other"],
  stress_levels: ["Low", "Medium", "High", "Very High"],
  limits: {
    age: limit(13, 100),
    avg_daily_usage_hours: limit(0, 24),
    daily_unlocks: limit(0, 2000),
    study_hours: limit(0, 24),
    physical_activity_hours: limit(0, 24),
    sleep_hours_per_night: limit(0, 24),
  },
  training_ranges: {
    age: limit(18, 24),
    avg_daily_usage_hours: limit(1, 8.8),
    daily_unlocks: limit(62, 273),
    study_hours: limit(0.3, 8.3),
    physical_activity_hours: limit(0, 4.1),
    sleep_hours_per_night: limit(3.6, 9.9),
  },
};

const VALID: FormValues = {
  age: "21",
  gender: "Female",
  country: "India",
  academic_level: "Undergraduate",
  most_used_platform: "Instagram",
  purpose_of_use: "Education",
  avg_daily_usage_hours: "4.5",
  daily_unlocks: "150",
  study_hours: "3",
  physical_activity_hours: "1,5",
  sleep_hours_per_night: "7",
  stress_level: "Medium",
};

describe("parseNumber", () => {
  it("reads dots and decimal commas", () => {
    expect(parseNumber("6.5")).toBe(6.5);
    expect(parseNumber(" 6,5 ")).toBe(6.5);
  });
  it("never turns empty or blank input into zero", () => {
    expect(parseNumber("")).toBeNaN();
    expect(parseNumber("   ")).toBeNaN();
  });
  it("rejects text", () => {
    expect(parseNumber("abc")).toBeNaN();
  });
});

describe("validateField", () => {
  it("requires a number and names the allowed range", () => {
    expect(validateField("sleep_hours_per_night", "", OPTIONS)).toBe("Enter a number.");
    expect(validateField("sleep_hours_per_night", "25", OPTIONS)).toBe("Enter a value between 0 and 24.");
    expect(validateField("sleep_hours_per_night", "-1", OPTIONS)).toBe("Enter a value between 0 and 24.");
    expect(validateField("sleep_hours_per_night", "7.5", OPTIONS)).toBeUndefined();
  });
  it("requires whole numbers for age and unlocks", () => {
    expect(validateField("age", "21.5", OPTIONS)).toBe("Enter a whole number.");
    expect(validateField("daily_unlocks", "99.9", OPTIONS)).toBe("Enter a whole number.");
  });
  it("enforces the same age limits as the server", () => {
    expect(validateField("age", "12", OPTIONS)).toBe("Enter a value between 13 and 100.");
    expect(validateField("age", "101", OPTIONS)).toBe("Enter a value between 13 and 100.");
    expect(validateField("age", "13", OPTIONS)).toBeUndefined();
  });
  it("accepts ages outside the training range (the server only warns)", () => {
    expect(validateField("age", "40", OPTIONS)).toBeUndefined();
  });
  it("requires a choice and only the listed ones", () => {
    expect(validateField("gender", "", OPTIONS)).toBe("Choose an option.");
    expect(validateField("gender", "Alien", OPTIONS)).toBe("Choose one of the listed options.");
    expect(validateField("gender", "Male", OPTIONS)).toBeUndefined();
  });
});

describe("validateForm", () => {
  it("passes a complete valid form", () => {
    expect(validateForm(VALID, OPTIONS)).toEqual({});
  });
  it("reports every empty field on an empty form", () => {
    expect(Object.keys(validateForm(EMPTY_VALUES, OPTIONS))).toHaveLength(12);
  });
  it("finds the first invalid field in form order, not alphabetical order", () => {
    const errors = validateForm({ ...VALID, sleep_hours_per_night: "99", gender: "" }, OPTIONS);
    expect(firstInvalidField(errors)).toBe("gender");
  });
});

describe("toRequest", () => {
  it("converts text to numbers and keeps choices as they are", () => {
    const request = toRequest(VALID);
    expect(request.age).toBe(21);
    expect(request.physical_activity_hours).toBe(1.5);
    expect(request.country).toBe("India");
  });
});

describe("issuesToErrors", () => {
  it("maps server issues to fields and ignores unknown names", () => {
    const errors = issuesToErrors([
      { field: "age", message: "Too low" },
      { field: "age", message: "Second message" },
      { field: "body", message: "Bad JSON" },
    ]);
    expect(errors).toEqual({ age: "Too low" });
  });
});

import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";

// Runs against the real backend. Option labels below come from the real model's categories.
async function fillForm(page: Page) {
  await page.getByLabel("Age").fill("21");
  await page.getByLabel("Gender").selectOption({ label: "Female" });
  await page.getByLabel("Academic level").selectOption({ label: "Undergraduate" });
  await page.getByLabel("Country").selectOption({ label: "India" });
  await page.getByLabel("Most-used platform").selectOption({ label: "Instagram" });
  await page.getByLabel("Main reason you use it").selectOption({ label: "Entertainment" });
  await page.getByLabel("Daily phone use").fill("4.5");
  await page.getByLabel("Phone unlocks per day").fill("150");
  await page.getByLabel("Study time").fill("3");
  await page.getByLabel("Physical activity").fill("1.5");
  await page.getByLabel("Sleep").fill("7");
  await page.getByLabel("Stress level").selectOption({ label: "Medium" });
}

test("a visitor fills in the form and sees an estimate", async ({ page }) => {
  await page.goto("/");
  await fillForm(page);
  await page.getByRole("button", { name: "Estimate my score" }).click();
  await expect(page.locator(".result__score")).toHaveText(/^\d\.\d$/);
  await expect(page.getByText(/typical range/)).toBeVisible();
  await expect(page.getByText(/not a diagnosis/)).toBeVisible();
});

test("an empty submit shows errors and does not call the API", async ({ page }) => {
  let predictCalls = 0;
  await page.route("**/api/predict", (route) => {
    predictCalls += 1;
    return route.continue();
  });
  await page.goto("/");
  await page.getByRole("button", { name: "Estimate my score" }).click();
  await expect(page.getByLabel("Age")).toBeFocused();
  expect(predictCalls).toBe(0);
});

test("works at phone width without sideways scrolling", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 800 });
  await page.goto("/");
  await expect(page.getByLabel("Age")).toBeVisible();
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBeLessThanOrEqual(0);
});

test("shows a clear error when the API is unreachable", async ({ page }) => {
  await page.route("**/api/options", (route) => route.abort());
  await page.goto("/");
  await expect(page.getByRole("alert")).toContainText("Can't reach the server");
});

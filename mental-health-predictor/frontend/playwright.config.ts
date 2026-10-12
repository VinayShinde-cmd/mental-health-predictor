import { defineConfig } from "@playwright/test";

// Start the backend and `npm run dev` first (see README), or set E2E_BASE_URL to a deployed staging URL.
export default defineConfig({
  testDir: "./e2e",
  reporter: "list",
  use: { baseURL: process.env.E2E_BASE_URL ?? "http://localhost:5173" },
});

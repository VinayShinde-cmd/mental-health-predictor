import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// In development the browser talks to this dev server, which forwards /api to the backend, so no CORS
// setup is needed locally. In production the built files call VITE_API_BASE_URL (see .env.example).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/api": "http://localhost:8000" },
  },
  build: { sourcemap: false },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    include: ["src/**/*.test.{ts,tsx}"],
    css: false,
  },
});

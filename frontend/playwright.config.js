import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.E2E_BASE_URL || "http://localhost:3000";
const apiURL = process.env.E2E_API_URL || "http://localhost:5000";

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  retries: process.env.CI ? 1 : 0,
  use: {
    baseURL,
    trace: "on-first-retry",
    extraHTTPHeaders: {},
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: process.env.CI
    ? undefined
    : [
        {
          command: "npm run dev -- --host 127.0.0.1 --port 3000",
          url: baseURL,
          reuseExistingServer: true,
          timeout: 120_000,
        },
      ],
  metadata: { apiURL },
});

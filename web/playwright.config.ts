import { defineConfig, devices } from "@playwright/test";

// SOS-0017 browser gate. One spec drives both viewport projects against a
// branch-local server (see web/e2e/server.mjs); the viewport matrix is the
// mobile 390x844 descriptor and an explicit 1440x900 desktop viewport, because
// Playwright's own default is 1280x720.
const PORT = Number(process.env.E2E_PORT ?? 4173);
const BASE_URL = process.env.E2E_BASE_URL ?? `http://127.0.0.1:${PORT}`;
const ARTIFACTS = "e2e/.artifacts";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  // One sequential browser walk per project: the vision receipt is merged from
  // both projects, so the two writers must not overlap.
  workers: 1,
  timeout: 120_000,
  expect: { timeout: 15_000 },
  reporter: [
    ["list"],
    ["html", { outputFolder: "playwright-report", open: "never" }],
    ["json", { outputFile: `${ARTIFACTS}/playwright-report.json` }],
  ],
  outputDir: `${ARTIFACTS}/test-results`,
  use: {
    baseURL: BASE_URL,
    testIdAttribute: "data-testid",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "mobile",
      use: {
        ...devices["iPhone 12"],
        browserName: "chromium",
        viewport: { width: 390, height: 844 },
      },
    },
    {
      name: "desktop",
      use: {
        browserName: "chromium",
        viewport: { width: 1440, height: 900 },
      },
    },
  ],
  webServer: {
    command: "node e2e/server.mjs",
    url: `${BASE_URL}/api/health`,
    reuseExistingServer: !process.env.CI,
    timeout: 180_000,
    stdout: "pipe",
    stderr: "pipe",
  },
});

// Branch-local server for the SOS-0017 browser gate.
//
// It serves the built SPA (web/dist) and the real API from one origin, against a
// throwaway Postgres database, with the deterministic offline tutor stand-in
// enabled (src/study_os/web/e2e_stub.py). It never points at the live site and
// it strips hosted model credentials from the child environment, so a gate run
// cannot spend money or reach a production provider.
//
// Required: E2E_DATABASE_URL (or TEST_DATABASE_URL) pointing at a throwaway
// database the caller owns. Optional: E2E_PORT, E2E_PYTHON.

import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const E2E_DIR = path.dirname(fileURLToPath(import.meta.url));
const WEB_DIR = path.resolve(E2E_DIR, "..");
const REPO_ROOT = path.resolve(WEB_DIR, "..");

const PORT = Number(process.env.E2E_PORT ?? 4173);
const HOST = "127.0.0.1";
const BASE_URL = process.env.E2E_BASE_URL ?? `http://${HOST}:${PORT}`;
const DIST = path.join(WEB_DIR, "dist");
const DATABASE_URL = process.env.E2E_DATABASE_URL ?? process.env.TEST_DATABASE_URL ?? "";

function fail(message) {
  console.error(`[e2e-server] ${message}`);
  process.exit(1);
}

if (!DATABASE_URL) {
  fail(
    "set E2E_DATABASE_URL (or TEST_DATABASE_URL) to a throwaway Postgres database; " +
      "the gate never runs against the live site",
  );
}
if (!existsSync(path.join(DIST, "index.html"))) {
  fail(`no built frontend at ${DIST}; run "npm run build" before the gate`);
}

const childEnv = { ...process.env };
// Hosted credentials must never reach the gate server.
for (const key of ["INFERHUB_API_KEY", "OPENROUTER_API_KEY"]) delete childEnv[key];
Object.assign(childEnv, {
  PYTHONPATH: path.join(REPO_ROOT, "src"),
  DATABASE_URL,
  STATIC_DIR: DIST,
  COOKIE_SECURE: "0",
  SERVER_SECRET: "e2e-gate-not-a-secret",
  PUBLIC_BASE_URL: BASE_URL,
  ALLOWED_ORIGINS: `${BASE_URL},http://localhost:${PORT}`,
  RATE_PER_IP_PER_MIN: "100000",
  RATE_PER_USER_PER_MIN: "100000",
  RATE_SIGNUP_PER_HOUR: "100000",
  DECISION_MODEL_ENABLED: "0",
  LLM_ENABLED: "1",
  STUDY_OS_E2E: "1",
  STUDY_OS_E2E_STUB_LLM: "1",
});

const python = process.env.E2E_PYTHON ?? "python";
const child = spawn(
  python,
  ["-m", "uvicorn", "study_os.web.api:app_factory", "--factory", "--host", HOST, "--port", String(PORT), "--log-level", "warning"],
  { cwd: WEB_DIR, env: childEnv, stdio: ["ignore", "pipe", "pipe"] },
);

child.stdout.on("data", (chunk) => process.stdout.write(chunk));
child.stderr.on("data", (chunk) => process.stderr.write(chunk));
child.on("error", (error) => fail(`could not start ${python}: ${error.message}`));
child.on("exit", (code) => process.exit(code ?? 1));

for (const signal of ["SIGINT", "SIGTERM"]) {
  process.on(signal, () => child.kill(signal));
}

console.log(`[e2e-server] serving ${DIST} at ${BASE_URL} against a throwaway database`);

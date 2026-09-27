// Cheap-vision judge for the SOS-0017 gate: InferHub hosted vision only, no OCR.
//
// Model policy (docs/webapp/SOS-0017_E2E_VISION_GATE_SDD.md): primary
// "ali/qwen3.8-flash", fallback "cb/deepseek-v4.1-flash" on transport, auth or
// quota failure only. Every verdict records the model that produced it
// (vision_model) so a fallback can never silently change gate semantics, and a
// provider failure is reported as VISION_PROVIDER_ERROR instead of being
// laundered into a pass. "zai/glm-4.6v" and "zai/glm-5.3-flash" are excluded.

import { readFile, stat } from "node:fs/promises";
import path from "node:path";
import {
  MALFORMED_CODE,
  NOT_RUN_CODE,
  PROVIDER_ERROR_CODE,
  VISION_PROMPT,
  parseLocator,
  parseVerdictCode,
  type VisionCode,
} from "./prompt";

export const PRIMARY_VISION_MODEL = "ali/qwen3.8-flash";
export const FALLBACK_VISION_MODEL = "cb/deepseek-v4.1-flash";

const DEFAULT_BASE_URL = "https://api.inferhub.dev/v1";
const REQUEST_TIMEOUT_MS = 60_000;

export const HOLDOUT_FIXTURE = "e2e/fixtures/review-holdout.json";

// Playwright runs the suite with the config directory (web/) as the cwd, so all
// gate paths are resolved from there instead of from a module-relative URL.
const WEB_DIR = process.cwd();
const E2E_DIR = path.join(WEB_DIR, "e2e");
const REPO_ROOT = path.dirname(WEB_DIR);

export type VisionVerdict = {
  vision_code: VisionCode;
  vision_locator: string;
  vision_model: string;
  vision_latency_ms: number;
  /** Which configured model answered, and whether a fallback was needed. */
  attempted_models: string[];
  note?: string;
};

export type HoldoutCase = {
  id: string;
  kind: "static" | "derived";
  image?: string;
  derived?: "review-panel-hidden";
  expect: VisionCode;
  description: string;
};

export type HoldoutFixture = {
  schema: string;
  cases: HoldoutCase[];
};

export function visionConfigured(): boolean {
  return Boolean(process.env.INFERHUB_API_KEY);
}

/** Paths named in the receipt are repo-relative so a verdict stays replayable. */
export function relativeToRepo(target: string): string {
  return path.relative(REPO_ROOT, path.resolve(target)).split(path.sep).join("/");
}

export async function imageExists(imagePath: string): Promise<boolean> {
  try {
    return (await stat(imagePath)).isFile();
  } catch {
    return false;
  }
}

export function visionBaseUrl(): string {
  return (process.env.INFERHUB_API_URL ?? DEFAULT_BASE_URL).replace(/\/+$/, "");
}

/** The blank/off-target control the judge must reject; see the fixture header. */
export async function loadHoldoutFixture(): Promise<HoldoutFixture> {
  const raw = await readFile(path.join(E2E_DIR, "fixtures", "review-holdout.json"), "utf8");
  return JSON.parse(raw) as HoldoutFixture;
}

async function askModel(model: string, imagePath: string, prompt: string): Promise<string> {
  const bytes = await readFile(imagePath);
  const body = {
    model,
    max_tokens: 200,
    temperature: 0,
    messages: [
      {
        role: "user",
        content: [
          { type: "text", text: prompt },
          {
            type: "image_url",
            image_url: { url: `data:image/png;base64,${bytes.toString("base64")}` },
          },
        ],
      },
    ],
  };
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const response = await fetch(`${visionBaseUrl()}/chat/completions`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${process.env.INFERHUB_API_KEY ?? ""}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    if (!response.ok) {
      throw new Error(`http:${response.status}`);
    }
    const payload = (await response.json()) as {
      choices?: { message?: { content?: string | null } }[];
    };
    return payload.choices?.[0]?.message?.content ?? "";
  } finally {
    clearTimeout(timer);
  }
}

/**
 * Judge one image. The primary model is tried first; the fallback is used only
 * when the primary could not answer at all. A returned verdict is never retried
 * or reinterpreted, and a malformed reply is a failure, not a pass.
 */
export async function judgeImage(imagePath: string): Promise<VisionVerdict> {
  const started = Date.now();
  if (!visionConfigured()) {
    return {
      vision_code: NOT_RUN_CODE,
      vision_locator: "no INFERHUB_API_KEY configured",
      vision_model: PRIMARY_VISION_MODEL,
      vision_latency_ms: 0,
      attempted_models: [],
      note: "vision not run: no credential configured",
    };
  }

  const attempted: string[] = [];
  const failures: string[] = [];
  for (const model of [PRIMARY_VISION_MODEL, FALLBACK_VISION_MODEL]) {
    attempted.push(model);
    let reply: string;
    try {
      reply = await askModel(model, imagePath, VISION_PROMPT);
    } catch (error) {
      failures.push(`${model}:${error instanceof Error ? error.message : String(error)}`);
      continue;
    }
    const code = parseVerdictCode(reply);
    return {
      vision_code: code,
      vision_locator: parseLocator(reply) || reply.trim().slice(0, 300),
      vision_model: model,
      vision_latency_ms: Date.now() - started,
      attempted_models: attempted,
      note:
        code === MALFORMED_CODE
          ? "judge reply did not start with a code from the closed set"
          : attempted.length > 1
            ? `fallback used after ${failures.join("; ")}`
            : undefined,
    };
  }

  return {
    vision_code: PROVIDER_ERROR_CODE,
    vision_locator: failures.join("; ").slice(0, 300),
    vision_model: attempted[attempted.length - 1] ?? PRIMARY_VISION_MODEL,
    vision_latency_ms: Date.now() - started,
    attempted_models: attempted,
    note: "all configured vision models failed; deterministic result stands alone",
  };
}

// Receipt writer for the SOS-0017 gate.
//
// The receipt is a *run output*, never a committed artifact: committing one
// would satisfy the shape contract with fabricated evidence. This module only
// declares the schema id, the marker path and the pure builders/mergers used by
// the spec; it never invents a checkpoint, a holdout result or a verdict.

import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import type { HoldoutCase, VisionVerdict } from "./judge";

export const RECEIPT_SCHEMA = "study_os.e2e.vision_gate_receipt/v0.1";
export const RECEIPT_MARKER_PATH = "web/e2e/.artifacts/vision-gate-receipt.json";

export const ARTIFACT_DIR = "e2e/.artifacts";
// Playwright runs the suite with the config directory (web/) as the cwd.
const E2E_DIR = path.join(process.cwd(), "e2e");

export type ReceiptCheckpoint = {
  id: string;
  project: string;
  viewport: { width: number; height: number };
  screenshot: string;
  image_sha256: string;
  deterministic: "PASS" | "FAIL";
  vision_code: string;
  vision_locator: string;
  vision_model: string;
  vision_latency_ms: number;
  note?: string;
};

export type ReceiptHoldoutCase = {
  id: string;
  screenshot: string;
  expect: string;
  vision_code: string;
  vision_model: string;
  result: "OK" | "HOLDOUT_BROKEN";
};

export type ReceiptHoldout = {
  result: "OK" | "HOLDOUT_BROKEN";
  cases: ReceiptHoldoutCase[];
};

export type ReceiptMetamorphic = {
  id: string;
  project: string;
  result: "PASS" | "FAIL";
  detail?: string;
};

export type Receipt = {
  schema: typeof RECEIPT_SCHEMA;
  run_id: string;
  git_sha: string | null;
  started_at: string;
  finished_at: string;
  projects: string[];
  checkpoints: ReceiptCheckpoint[];
  holdout: ReceiptHoldout;
  metamorphic: ReceiptMetamorphic[];
  verdict: "GREEN" | "RED" | "NOT_RUN";
  vision_run: boolean;
  notes: string[];
};

export function artifactDir(): string {
  return path.join(E2E_DIR, ".artifacts");
}

export function artifactRelative(file: string): string {
  return path.relative(E2E_DIR, file).split(path.sep).join("/");
}

/** Ordering is fixed so a merged receipt reads the same on every run. */
export const PROJECT_ORDER = ["mobile", "desktop"];
export const CHECKPOINT_ORDER = [
  "review.panel.initial",
  "review.receipt.after-submit",
  "review.panel.after-regen",
];
export const METAMORPHIC_ORDER = ["M-regen", "M-viewport", "M-submit", "M-noop"];

export function newReceipt(): Receipt {
  return {
    schema: RECEIPT_SCHEMA,
    run_id: crypto.randomUUID(),
    git_sha: null,
    started_at: new Date().toISOString(),
    finished_at: new Date().toISOString(),
    projects: [],
    checkpoints: [],
    holdout: { result: "OK", cases: [] },
    metamorphic: [],
    verdict: "NOT_RUN",
    vision_run: false,
    notes: [],
  };
}

function rank(list: readonly string[], value: string): number {
  const index = list.indexOf(value);
  return index === -1 ? list.length : index;
}

export function upsertCheckpoint(receipt: Receipt, checkpoint: ReceiptCheckpoint): void {
  const at = receipt.checkpoints.findIndex(
    (item) => item.id === checkpoint.id && item.project === checkpoint.project,
  );
  if (at === -1) receipt.checkpoints.push(checkpoint);
  else receipt.checkpoints[at] = checkpoint;
  receipt.checkpoints.sort(
    (a, b) =>
      rank(PROJECT_ORDER, a.project) - rank(PROJECT_ORDER, b.project) ||
      rank(CHECKPOINT_ORDER, a.id) - rank(CHECKPOINT_ORDER, b.id),
  );
}

export function upsertMetamorphic(receipt: Receipt, entry: ReceiptMetamorphic): void {
  const at = receipt.metamorphic.findIndex(
    (item) => item.id === entry.id && item.project === entry.project,
  );
  if (at === -1) receipt.metamorphic.push(entry);
  else receipt.metamorphic[at] = entry;
  receipt.metamorphic.sort(
    (a, b) =>
      rank(PROJECT_ORDER, a.project) - rank(PROJECT_ORDER, b.project) ||
      rank(METAMORPHIC_ORDER, a.id) - rank(METAMORPHIC_ORDER, b.id),
  );
}

export function upsertHoldoutCase(receipt: Receipt, entry: ReceiptHoldoutCase): void {
  const at = receipt.holdout.cases.findIndex((item) => item.id === entry.id);
  if (at === -1) receipt.holdout.cases.push(entry);
  else receipt.holdout.cases[at] = entry;
  receipt.holdout.cases.sort((a, b) => a.id.localeCompare(b.id));
  if (entry.result === "HOLDOUT_BROKEN") receipt.holdout.result = "HOLDOUT_BROKEN";
}

export function projectFinished(receipt: Receipt, project: string): void {
  if (!receipt.projects.includes(project)) receipt.projects.push(project);
  receipt.projects.sort((a, b) => rank(PROJECT_ORDER, a) - rank(PROJECT_ORDER, b));
}

export function addNote(receipt: Receipt, note: string): void {
  if (note && !receipt.notes.includes(note)) receipt.notes.push(note);
}

/**
 * The receipt verdict, mirroring the gate interpretation table: GREEN needs
 * every deterministic and metamorphic result to pass, the holdout to hold, and
 * at least one checkpoint corroborated by a real vision pass. A missing or
 * unusable credential is NOT_RUN, never green.
 */
export function computeVerdict(receipt: Receipt, expectedProjects: readonly string[]): Receipt["verdict"] {
  const complete =
    receipt.projects.length >= expectedProjects.length &&
    receipt.checkpoints.length > 0 &&
    receipt.checkpoints.every((item) => item.deterministic === "PASS") &&
    receipt.metamorphic.length > 0 &&
    receipt.metamorphic.every((item) => item.result === "PASS");
  if (!complete || receipt.holdout.result === "HOLDOUT_BROKEN") return "RED";
  const corroborated = receipt.checkpoints.some((item) => item.vision_code === "VISION_PASS");
  if (!receipt.vision_run || !corroborated) return "NOT_RUN";
  return "GREEN";
}

export function markFinished(receipt: Receipt): void {
  receipt.finished_at = new Date().toISOString();
}

export async function writeReceipt(receipt: Receipt, file: string): Promise<void> {
  await mkdir(path.dirname(file), { recursive: true });
  await writeFile(file, `${JSON.stringify(receipt, null, 2)}\n`, "utf8");
}

export async function readReceipt(file: string): Promise<Receipt | null> {
  try {
    return JSON.parse(await readFile(file, "utf8")) as Receipt;
  } catch {
    return null;
  }
}

export function applyVerdicts(receipt: Receipt, cases: HoldoutCase[]): void {
  // Bookkeeping only: each case must already have been judged and recorded.
  if (cases.some((item) => item.expect === "VISION_PASS")) {
    receipt.holdout.result = "HOLDOUT_BROKEN";
  }
}

export type { VisionVerdict };

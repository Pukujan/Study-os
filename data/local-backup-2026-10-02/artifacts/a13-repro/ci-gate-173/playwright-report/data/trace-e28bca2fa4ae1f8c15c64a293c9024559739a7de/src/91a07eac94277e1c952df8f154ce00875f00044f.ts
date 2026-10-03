// SOS-0017 browser gate for the learner step review (#126).
//
// Deterministic cases own correctness (real browser, real API, real database);
// the cheap-vision judge only corroborates that a human-shaped surface painted.
// Vision can never turn a deterministic failure green, a passing holdout voids
// the run, and a missing credential is reported as VISION_NOT_RUN rather than a
// pass. One spec drives both the mobile 390x844 and desktop 1440x900 projects.
//
// Metamorphic relations: M-regen (regeneration must not drop the review
// surface), M-viewport (a mid-flow viewport swap keeps every control), M-submit
// (a submitted review stays visible as a receipt) and M-noop (an idle reload
// changes nothing and posts nothing).

import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { expect, test, type Page } from "@playwright/test";
import {
  HOLDOUT_FIXTURE,
  imageExists,
  judgeImage,
  loadHoldoutFixture,
  relativeToRepo,
  visionConfigured,
  type HoldoutCase,
  type VisionVerdict,
} from "./vision/judge";
import { PASS_CODE, PROVIDER_ERROR_CODE, NOT_RUN_CODE } from "./vision/prompt";
import {
  ARTIFACT_DIR,
  RECEIPT_MARKER_PATH,
  addNote,
  artifactDir,
  artifactRelative,
  computeVerdict,
  markFinished,
  newReceipt,
  projectFinished,
  readReceipt,
  upsertCheckpoint,
  upsertHoldoutCase,
  upsertMetamorphic,
  writeReceipt,
  type Receipt,
  type ReceiptCheckpoint,
} from "./vision/receipt";

const PANEL = "player.review.panel";
const SUBMITTED = "player.review.submitted";
const WHY = "player.review.why";
const SUBMIT = "player.review.submit";
const SCORES = [1, 2, 3, 4, 5].map((score) => `player.review.score-${score}`);
const EXPECTED_PROJECTS = ["mobile", "desktop"];
const WHY_TEXT = "The box helped; the index label was unclear.";
// The judge is a network round trip to a cheap hosted model; a mobile full-page
// capture can take tens of seconds to score. This budget is the measured cost of
// a real call, not slack for retrying a flaky verdict.
const JUDGE_TIMEOUT_MS = 240_000;

function projectName(): string {
  return test.info().project.name;
}

function projectReceiptFile(project: string): string {
  return path.join(artifactDir(), `vision-gate-receipt.${project}.json`);
}

function artifactFile(name: string): string {
  return path.join(artifactDir(), name);
}

function gitSha(): string | null {
  if (process.env.GITHUB_SHA) return process.env.GITHUB_SHA;
  try {
    return execFileSync("git", ["rev-parse", "HEAD"], { encoding: "utf8" }).trim();
  } catch {
    return null;
  }
}

async function sha256(file: string): Promise<string> {
  return createHash("sha256").update(await readFile(file)).digest("hex");
}

async function loadProjectReceipt(project: string): Promise<Receipt> {
  const existing = await readReceipt(projectReceiptFile(project));
  if (existing) return existing;
  const receipt = newReceipt();
  receipt.git_sha = gitSha();
  receipt.projects = [project];
  return receipt;
}

async function saveProjectReceipt(receipt: Receipt, project: string): Promise<void> {
  await writeReceipt(receipt, projectReceiptFile(project));
}

/** Start a lesson as a guest and wait for the review surface to paint. */
async function openPlayer(page: Page): Promise<void> {
  await page.goto("/");
  await page.locator('[data-track="try.start"]').first().click();
  await expect(page).toHaveURL(/\/play\//);
  await expect(page.getByTestId(PANEL)).toBeVisible();
}

/** D1/D2/D3: the panel, the five ratings, the why field and the Submit gate. */
async function expectReviewControls(page: Page, { submitEnabled }: { submitEnabled: boolean }) {
  await expect(page.getByTestId(PANEL)).toBeVisible();
  for (const score of SCORES) {
    const control = page.getByTestId(score);
    await expect(control).toBeVisible();
    await expect(control).toBeEnabled();
  }
  await expect(page.getByTestId(WHY)).toBeVisible();
  await expect(page.getByTestId(WHY)).toBeEditable();
  await expect(page.getByTestId(SUBMIT)).toBeVisible();
  if (submitEnabled) await expect(page.getByTestId(SUBMIT)).toBeEnabled();
  else await expect(page.getByTestId(SUBMIT)).toBeDisabled();
}

async function draftReview(page: Page, score = 3): Promise<void> {
  await page.getByTestId(`player.review.score-${score}`).click();
  await page.getByTestId(WHY).fill(WHY_TEXT);
  await expect(page.getByTestId(SUBMIT)).toBeEnabled();
}

async function progressLabel(page: Page): Promise<string> {
  return (await page.locator('[aria-label^="Progress "]').first().getAttribute("aria-label")) ?? "";
}

async function shoot(page: Page, project: string, name: string): Promise<string> {
  await mkdir(path.join(artifactDir(), project), { recursive: true });
  const file = artifactFile(path.join(project, `${name}.png`));
  // Full page, but at CSS scale: the layout is identical and the judged image is
  // not blown up by the device pixel ratio (mobile is 3x), which is what makes
  // the provider round trip slow.
  await page.screenshot({ path: file, fullPage: true, scale: "css" });
  return file;
}

/**
 * Judge one screenshot and record it. A fail code fails the run (vision looked
 * and did not see the surface); a provider error or a missing credential only
 * downgrades the run to NOT_RUN, because that is not evidence about the UI.
 */
async function recordCheckpoint(
  project: string,
  receipt: Receipt,
  {
    id,
    page,
    deterministic,
  }: { id: string; page: Page; deterministic: "PASS" | "FAIL" },
): Promise<VisionVerdict> {
  const file = await shoot(page, project, id);
  const viewport = page.viewportSize() ?? { width: 0, height: 0 };
  const verdict = await judgeImage(file);
  const checkpoint: ReceiptCheckpoint = {
    id,
    project,
    viewport,
    screenshot: artifactRelative(file),
    image_sha256: await sha256(file),
    deterministic,
    vision_code: verdict.vision_code,
    vision_locator: verdict.vision_locator,
    vision_model: verdict.vision_model,
    vision_latency_ms: verdict.vision_latency_ms,
    note: verdict.note,
  };
  upsertCheckpoint(receipt, checkpoint);
  if (verdict.vision_code === PASS_CODE) receipt.vision_run = true;
  else if (verdict.vision_code === PROVIDER_ERROR_CODE) addNote(receipt, `vision provider error at ${id}`);
  else if (verdict.vision_code === NOT_RUN_CODE) addNote(receipt, "vision not run: no credential configured");
  else addNote(receipt, `vision ${verdict.vision_code} at ${id}`);
  await test.info().attach(`${project}-${id}.png`, { path: file, contentType: "image/png" });
  await saveProjectReceipt(receipt, project);
  return verdict;
}

/** V1/V2: a real checkpoint must be corroborated, unless vision is unavailable. */
function expectVisionPass(verdict: VisionVerdict, checkpoint: string): void {
  if (verdict.vision_code === PASS_CODE) return;
  if (verdict.vision_code === PROVIDER_ERROR_CODE || verdict.vision_code === NOT_RUN_CODE) {
    test.info().annotations.push({
      type: "vision-not-run",
      description: `${checkpoint}: ${verdict.vision_code} (${verdict.vision_locator})`,
    });
    return;
  }
  expect(
    verdict.vision_code,
    `${checkpoint}: the judge did not see the review surface (${verdict.vision_locator})`,
  ).toBe(PASS_CODE);
}

test.describe("learner step review: deterministic surface", () => {
  test("D1/D2/D3/D5 panel, five ratings, why, Submit gate and a screenshot per checkpoint", async ({ page }) => {
    test.setTimeout(JUDGE_TIMEOUT_MS);
    const project = projectName();
    const receipt = await loadProjectReceipt(project);
    let posts = 0;
    page.on("request", (request) => {
      if (request.method() === "POST" && request.url().includes("/api/feedback")) posts += 1;
    });

    await openPlayer(page);
    await expectReviewControls(page, { submitEnabled: false });

    // D2: choosing a score marks it and still does not post anything.
    await page.getByTestId("player.review.score-3").click();
    await expect(page.getByTestId("player.review.score-3")).toHaveAttribute("aria-pressed", "true");
    await expect(page.getByTestId(SUBMIT)).toBeDisabled();

    // D3: Submit stays closed until a nonblank why is typed.
    await page.getByTestId(WHY).fill("   ");
    await expect(page.getByTestId(SUBMIT)).toBeDisabled();
    await page.getByTestId(WHY).fill(WHY_TEXT);
    await expect(page.getByTestId(SUBMIT)).toBeEnabled();
    expect(posts, "choosing a score or typing must not post a review").toBe(0);

    const verdict = await recordCheckpoint(project, receipt, {
      id: "review.panel.initial",
      page,
      deterministic: "PASS",
    });
    expectVisionPass(verdict, "review.panel.initial");
    projectFinished(receipt, project);
    await saveProjectReceipt(receipt, project);
  });
});

test.describe("learner step review: metamorphic relations", () => {
  test("M-regen regeneration keeps the whole review surface and posts nothing", async ({ page }) => {
    test.setTimeout(JUDGE_TIMEOUT_MS);
    const project = projectName();
    const receipt = await loadProjectReceipt(project);
    let posts = 0;
    page.on("request", (request) => {
      if (request.method() === "POST" && request.url().includes("/api/feedback")) posts += 1;
    });

    await openPlayer(page);
    await draftReview(page, 3);
    const before = await page.locator(".teach.card").first().innerText();
    const progressBefore = await progressLabel(page);

    // The regeneration control family is the chat path to a re-render.
    const regen = page.locator('[data-testid^="player.step.regen-"]');
    await expect(regen.first()).toBeVisible();
    // The regeneration path asks the tutor for another render of the same step.
    const tutorCall = page.waitForRequest(
      (request) => request.method() === "POST" && request.url().includes("/api/player/sessions/") && request.url().endsWith("/tutor"),
      { timeout: 30_000 },
    );
    await regen.first().click();
    await tutorCall;

    await expect
      .poll(async () => page.locator(".teach.card").first().innerText(), { timeout: 30_000 })
      .not.toBe(before);

    await expectReviewControls(page, { submitEnabled: true });
    await expect(page.getByTestId(SUBMITTED)).toHaveCount(0);
    expect(await progressLabel(page)).toBe(progressBefore);
    expect(posts, "regenerating a presentation must not post a review").toBe(0);

    const verdict = await recordCheckpoint(project, receipt, {
      id: "review.panel.after-regen",
      page,
      deterministic: "PASS",
    });
    expectVisionPass(verdict, "review.panel.after-regen");
    upsertMetamorphic(receipt, { id: "M-regen", project, result: "PASS" });
    await saveProjectReceipt(receipt, project);
  });

  test("M-viewport a mid-flow 1440x900 -> 390x844 swap keeps every control on canvas", async ({ page }) => {
    const project = projectName();
    const receipt = await loadProjectReceipt(project);

    await openPlayer(page);
    await page.setViewportSize({ width: 1440, height: 900 });
    await expectReviewControls(page, { submitEnabled: false });

    await page.setViewportSize({ width: 390, height: 844 });
    await draftReview(page, 4);

    const box = await page.getByTestId(SUBMIT).boundingBox();
    expect(box, "Submit must be laid out, not detached").not.toBeNull();
    expect(box?.width ?? 0).toBeGreaterThan(0);
    expect(box?.height ?? 0).toBeGreaterThan(0);
    expect(box?.x ?? -1).toBeGreaterThanOrEqual(0);
    expect((box?.x ?? 0) + (box?.width ?? 0)).toBeLessThanOrEqual(391);
    expect(box?.y ?? -1).toBeGreaterThanOrEqual(0);
    await page.getByTestId(SUBMIT).scrollIntoViewIfNeeded();
    await expect(page.getByTestId(SUBMIT)).toBeInViewport();

    upsertMetamorphic(receipt, { id: "M-viewport", project, result: "PASS" });
    await saveProjectReceipt(receipt, project);
  });

  test("M-submit one Submit posts once and leaves a visible receipt", async ({ page }) => {
    test.setTimeout(JUDGE_TIMEOUT_MS);
    const project = projectName();
    const receipt = await loadProjectReceipt(project);
    const posts: string[] = [];
    page.on("request", (request) => {
      if (request.method() === "POST" && request.url().includes("/api/feedback")) posts.push(request.url());
    });

    await openPlayer(page);
    const progressBefore = await progressLabel(page);
    await draftReview(page, 3);
    await page.getByTestId(SUBMIT).click();

    await expect(page.getByTestId(SUBMITTED)).toBeVisible();
    await expect(page.getByTestId(PANEL)).toBeVisible();
    expect(await progressLabel(page)).toBe(progressBefore);
    expect(posts.length, "one Submit is exactly one review request").toBe(1);

    const verdict = await recordCheckpoint(project, receipt, {
      id: "review.receipt.after-submit",
      page,
      deterministic: "PASS",
    });
    expectVisionPass(verdict, "review.receipt.after-submit");
    upsertMetamorphic(receipt, { id: "M-submit", project, result: "PASS" });
    await saveProjectReceipt(receipt, project);
  });

  test("M-noop an idle reload keeps the same control set and posts nothing", async ({ page }) => {
    const project = projectName();
    const receipt = await loadProjectReceipt(project);
    let posts = 0;
    page.on("request", (request) => {
      if (request.method() === "POST" && request.url().includes("/api/feedback")) posts += 1;
    });

    await openPlayer(page);
    await expectReviewControls(page, { submitEnabled: false });
    const before = await progressLabel(page);

    await page.reload();
    await expect(page.getByTestId(PANEL)).toBeVisible();
    await expectReviewControls(page, { submitEnabled: false });
    await expect(page.getByTestId(SUBMITTED)).toHaveCount(0);
    expect(await progressLabel(page)).toBe(before);
    expect(posts, "an idle reload must not post a review").toBe(0);

    upsertMetamorphic(receipt, { id: "M-noop", project, result: "PASS" });
    await saveProjectReceipt(receipt, project);
  });
});

test.describe("blank-canvas holdout", () => {
  test("V3 the holdout images fail closed and a passing holdout voids the run", async ({ page }) => {
    test.setTimeout(JUDGE_TIMEOUT_MS);
    const project = projectName();
    const receipt = await loadProjectReceipt(project);
    const fixture = await loadHoldoutFixture();
    expect(fixture.cases.length, "the holdout must declare at least one negative case").toBeGreaterThan(0);
    // No holdout case may expect a pass: that is the false positive this gate catches.
    expect(fixture.cases.filter((item) => item.expect === PASS_CODE)).toEqual([]);

    // Derived control 1: the real player with the review panel removed.
    await openPlayer(page);
    await page.getByTestId(PANEL).evaluate((node) => {
      (node as HTMLElement).style.display = "none";
    });
    await expect(page.getByTestId(PANEL)).toBeHidden();
    const hidden = await shoot(page, project, "holdout-review-panel-hidden");

    // Static control 2: an empty canvas.
    await page.setContent("<html><body style='margin:0;background:#ffffff'></body></html>");
    const blank = await shoot(page, project, "holdout-blank-canvas");

    // Static control 3: a rendered interface that is not the review surface.
    await page.setContent(
      "<html><body style='margin:0;font-family:sans-serif;background:#f4f4f5'>" +
        "<header style='padding:12px;background:#1f2937;color:#fff'>Account settings</header>" +
        "<main style='padding:24px'><h1 style='font-size:20px'>Billing history</h1>" +
        "<table border='1' cellpadding='8'><tr><th>Invoice</th><th>Amount</th></tr>" +
        "<tr><td>INV-1042</td><td>$12.00</td></tr><tr><td>INV-1043</td><td>$9.50</td></tr></table></main>" +
        "</body></html>",
    );
    const unrelated = await shoot(page, project, "holdout-unrelated-screen");

    const images: Record<string, string> = {
      "review-panel-hidden": hidden,
      "blank-canvas": blank,
      "unrelated-screen": unrelated,
    };

    const verdicts: VisionVerdict[] = [];
    for (const holdoutCase of fixture.cases as HoldoutCase[]) {
      const key = holdoutCase.derived ?? path.basename(holdoutCase.image ?? "", ".png");
      const file = images[key];
      expect(file, `holdout case ${holdoutCase.id} has no captured image (${key})`).toBeTruthy();
      expect(await imageExists(file), `holdout image missing for ${holdoutCase.id}`).toBe(true);
      const verdict = await judgeImage(file);
      verdicts.push(verdict);
      upsertHoldoutCase(receipt, {
        id: holdoutCase.id,
        screenshot: artifactRelative(file),
        expect: holdoutCase.expect,
        vision_code: verdict.vision_code,
        vision_model: verdict.vision_model,
        result: verdict.vision_code === PASS_CODE ? "HOLDOUT_BROKEN" : "OK",
      });
      await test.info().attach(`${project}-${holdoutCase.id}.png`, { path: file, contentType: "image/png" });
    }
    projectFinished(receipt, project);
    await saveProjectReceipt(receipt, project);

    if (visionConfigured()) {
      for (const [index, verdict] of verdicts.entries()) {
        const holdoutCase = fixture.cases[index];
        if (verdict.vision_code === PROVIDER_ERROR_CODE || verdict.vision_code === NOT_RUN_CODE) {
          test.info().annotations.push({
            type: "vision-not-run",
            description: `${holdoutCase.id}: ${verdict.vision_code}`,
          });
          continue;
        }
        expect(
          verdict.vision_code,
          `holdout ${holdoutCase.id} must not pass: ${holdoutCase.description}`,
        ).not.toBe(PASS_CODE);
      }
    } else {
      test.info().annotations.push({
        type: "vision-not-run",
        description: "no INFERHUB_API_KEY: holdout captured but not judged (VISION_NOT_RUN)",
      });
    }

    await mergeReceipts();
  });
});

/** Merge the per-project receipts into the single declared marker receipt. */
async function mergeReceipts(): Promise<Receipt> {
  const merged = newReceipt();
  merged.git_sha = gitSha();
  for (const project of EXPECTED_PROJECTS) {
    const projectReceipt = await readReceipt(projectReceiptFile(project));
    if (!projectReceipt) continue;
    if (projectReceipt.started_at < merged.started_at) merged.started_at = projectReceipt.started_at;
    for (const checkpoint of projectReceipt.checkpoints) upsertCheckpoint(merged, checkpoint);
    for (const entry of projectReceipt.metamorphic) upsertMetamorphic(merged, entry);
    for (const entry of projectReceipt.holdout.cases) upsertHoldoutCase(merged, entry);
    for (const note of projectReceipt.notes) addNote(merged, note);
    merged.vision_run = merged.vision_run || projectReceipt.vision_run;
    projectFinished(merged, project);
  }
  merged.holdout.result = merged.holdout.cases.some((item) => item.result === "HOLDOUT_BROKEN")
    ? "HOLDOUT_BROKEN"
    : "OK";
  merged.verdict = computeVerdict(merged, EXPECTED_PROJECTS);
  markFinished(merged);
  const marker = path.join(process.cwd(), RECEIPT_MARKER_PATH.replace(/^web\//, ""));
  await writeReceipt(merged, marker);
  await writeFile(
    artifactFile("vision-gate-summary.txt"),
    `${merged.verdict} checkpoints=${merged.checkpoints.length} metamorphic=${merged.metamorphic.length} ` +
      `holdout=${merged.holdout.result} vision_run=${merged.vision_run}\n`,
    "utf8",
  );
  await test.info().attach("vision-gate-receipt.json", { path: marker, contentType: "application/json" });
  return merged;
}

test("the gate declares its artifact layout and holdout wiring", async () => {
  expect(ARTIFACT_DIR).toBe("e2e/.artifacts");
  expect(HOLDOUT_FIXTURE).toBe("e2e/fixtures/review-holdout.json");
  const fixture = JSON.parse(await readFile(path.join(process.cwd(), "e2e", "fixtures", "review-holdout.json"), "utf8"));
  expect(fixture.schema).toContain("holdout");
  expect(fixture.cases.every((item: HoldoutCase) => item.expect !== PASS_CODE)).toBe(true);
  expect(relativeToRepo(path.join(process.cwd(), "e2e", "fixtures", "review-holdout.json"))).toBe(
    "web/e2e/fixtures/review-holdout.json",
  );
});

const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE = process.env.E2E_BASE_URL || "https://study.design-bakery.com";
const ART = process.env.ART_DIR || path.join(__dirname);
const SHOTS = path.join(ART, "screenshots");
const HEADLESS = process.env.HEADED !== "1";
const CHAT_TIMEOUT_MS = 20000;
const NAV_TIMEOUT = 45000;

fs.mkdirSync(SHOTS, { recursive: true });

const controlsTried = [];
const defects = [];
const checks = [];

function utcNow() {
  return new Date().toISOString();
}

function recordControl(name, detail = {}) {
  controlsTried.push({ t: utcNow(), name, ...detail });
}

function addCheck(id, ok, detail, severity = "P1") {
  const row = { id, ok: !!ok, detail: String(detail || ""), severity };
  checks.push(row);
  if (!ok) {
    defects.push({
      id,
      severity,
      title: id,
      detail: String(detail || ""),
      repro: detail && detail.repro ? detail.repro : undefined,
    });
  }
  console.log(`${ok ? "PASS" : "FAIL"} [${severity}] ${id}: ${typeof detail === "string" ? detail : JSON.stringify(detail)}`);
}

function addDefect(severity, id, detail, repro) {
  defects.push({ id, severity, title: id, detail: String(detail), repro: repro || "" });
  checks.push({ id, ok: false, detail: String(detail), severity });
  console.log(`FAIL [${severity}] ${id}: ${detail}`);
}

function note(id, detail) {
  checks.push({ id, ok: true, detail: String(detail), severity: "info" });
  console.log(`NOTE ${id}: ${detail}`);
}

async function shot(page, name) {
  const file = path.join(SHOTS, `${name}.png`);
  try {
    await page.screenshot({ path: file, fullPage: true });
  } catch (e) {
    console.log("screenshot failed", name, e.message);
  }
  return file;
}

async function safeClick(page, locator, name, opts = {}) {
  recordControl(name, { action: "click" });
  try {
    const loc = locator.first();
    await loc.waitFor({ state: "visible", timeout: opts.timeout || 8000 });
    const tries = opts.waitEnabledTries || 40;
    for (let i = 0; i < tries; i++) {
      if (await loc.isEnabled().catch(() => false)) break;
      await page.waitForTimeout(250);
    }
    if (!(await loc.isEnabled().catch(() => false))) {
      recordControl(name, { action: "click-disabled" });
      return false;
    }
    await loc.click({ timeout: 8000, force: !!opts.force });
    return true;
  } catch (e) {
    recordControl(name, { action: "click-fail", error: e.message });
    return false;
  }
}

function textBlob(t) {
  return (t || "").replace(/\s+/g, " ").trim();
}

async function bodyText(page) {
  return textBlob(await page.locator("body").innerText().catch(() => ""));
}

async function isBlankWhite(page) {
  return page.evaluate(() => {
    const body = document.body;
    if (!body) return true;
    const text = (body.innerText || "").trim();
    const kids = body.querySelectorAll("img, canvas, svg, button, a, input, .card, .teach, .probe, .try-page, .home-lanes");
    const bg = getComputedStyle(body).backgroundColor;
    const main = document.querySelector("main");
    const mainBg = main ? getComputedStyle(main).backgroundColor : bg;
    const looksWhite = /rgb\(\s*255,\s*255,\s*255\s*\)|#fff|transparent|rgba\(0,\s*0,\s*0,\s*0\)/i.test(mainBg + bg);
    return text.length < 8 && kids.length < 2 && looksWhite;
  });
}

async function teachFingerprint(page) {
  return page.evaluate(() => {
    const teach = document.querySelector("section.teach, .teach.card");
    if (!teach) return { present: false, text: "", html: "", frames: 0 };
    return {
      present: true,
      text: (teach.innerText || "").slice(0, 2000),
      html: teach.innerHTML.slice(0, 4000),
      frames: teach.querySelectorAll(".frame, [class*='frame'], svg, canvas, img").length,
    };
  });
}

async function run() {
  const browser = await chromium.launch({ headless: HEADLESS });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    ignoreHTTPSErrors: true,
  });
  const page = await context.newPage();
  page.setDefaultTimeout(15000);
  const consoleErrors = [];
  page.on("pageerror", (e) => consoleErrors.push(String(e)));
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });

  try {
    // ========== HOME / TRY (guest) ==========
    await page.goto(BASE + "/", { waitUntil: "domcontentloaded", timeout: NAV_TIMEOUT });
    await page.waitForTimeout(1500);
    await shot(page, "01-home");

    const startBtns = page.locator('[data-track="try.start"], [data-track="home.continue"], [data-track="home.lesson.start"]');
    const startCount = await startBtns.count();
    recordControl("home.start-or-resume", { count: startCount });
    addCheck(
      "A-home-start-resume",
      startCount > 0,
      `Guest Start/Resume/Try controls visible: ${startCount}`,
      "P0"
    );

    // A23: classic DSA PIR not primary
    const classic = page.locator('[data-track="home.dsa.classic"], [data-track="home.dsa"]');
    const classicCount = await classic.count();
    const classicPrimary = page.locator(".btn.primary[data-track='home.dsa.classic'], .btn.primary[data-track='home.dsa']");
    const classicPrimaryCount = await classicPrimary.count();
    const body = await bodyText(page);
    const classicTextPrimary =
      /classic\s+sliding|classic\s+dsa|dsa\s+pir|PIR\s+path/i.test(body) &&
      (await page.locator(".btn.primary, .continue-btn").filter({ hasText: /classic|PIR|sliding-window lesson/i }).count()) > 0;
    addCheck(
      "A23-no-classic-dsa-pir-primary",
      classicPrimaryCount === 0 && !classicTextPrimary,
      `classic track attrs=${classicCount} primary=${classicPrimaryCount} textPrimary=${classicTextPrimary}`,
      "P1"
    );

    // Catalog (Try page lists lessons)
    const want = [
      { id: "catalog-hesi-fractions", re: /Comparing fractions|fractions-compare/i, sev: "P1" },
      { id: "catalog-dsa-big-o", re: /Big O|big-o-growth-families|how work grows/i, sev: "P1" },
      { id: "catalog-sliding-window", re: /Sliding window|sliding-window-box/i, sev: "P2" },
    ];
    for (const w of want) {
      const ok = w.re.test(body);
      addCheck(w.id, ok, ok ? "listed on guest home/try" : "NOT listed on guest home/try", w.sev);
    }

    // Prefer Big O if listed; else first Try
    let started = false;
    const bigOTry = page.locator(".lesson-item").filter({ hasText: /Big O|how work grows/i }).locator('[data-track="try.start"]');
    if ((await bigOTry.count()) > 0) {
      started = await safeClick(page, bigOTry, "try.start-big-o");
    } else {
      started = await safeClick(page, page.locator('[data-track="try.start"]').first(), "try.start-first");
    }

    if (!started) {
      addDefect("P0", "A18-start-navigation", "Could not click Start/Try", "Open /, click Try it / Try on a lesson");
      await shot(page, "fail-start-click");
    } else {
      try {
        await page.waitForURL(/\/play\//, { timeout: 20000 });
      } catch {
        addDefect("P0", "A18-start-url", `After Start URL is ${page.url()}, expected /play/`, "Click Try/Start from guest home");
        await shot(page, "fail-start-url");
      }
      await page.waitForTimeout(2000);
      await shot(page, "02-after-start");

      const blank = await isBlankWhite(page);
      const playBody = await bodyText(page);
      const hasPlayerChrome =
        /Explain again|Worked example|Continue|How useful|Ask the tutor|Study buddy|Big O|fraction/i.test(playBody) ||
        (await page.locator("section.teach, section.probe, [data-testid='player.review.panel']").count()) > 0;
      addCheck(
        "A18-no-blank-white-play",
        !blank && hasPlayerChrome,
        blank ? "Blank/white play surface after Start" : `play chrome ok; textLen=${playBody.length}`,
        "P0"
      );
      if (blank || !hasPlayerChrome) await shot(page, "fail-A18-blank");
    }

    // ========== PLAYER ==========
    if (/\/play\//.test(page.url())) {
      await page.waitForTimeout(1000);
      const phaseText = await bodyText(page);

      const hasTeach = (await page.locator("section.teach, .teach.card").count()) > 0;
      const hasProbe = (await page.locator("section.probe, .probe.card").count()) > 0;
      const hasContinue = (await page.locator('[data-testid="player.teach-continue"], [data-track="player.next"]').count()) > 0;
      note("player-phase-snapshot", `teach=${hasTeach} probe=${hasProbe} continue=${hasContinue} url=${page.url()}`);

      // Teach vs probe presence (soft)
      addCheck(
        "player-teach-or-probe",
        hasTeach || hasProbe || hasContinue,
        `teach=${hasTeach} probe=${hasProbe} continue=${hasContinue}`,
        "P0"
      );

      // A12c: teach must not spoil probe answers on same screen
      if (hasTeach && hasProbe) {
        const spoil = await page.evaluate(() => {
          const teach = document.querySelector("section.teach, .teach.card");
          const probe = document.querySelector("section.probe, .probe.card");
          if (!teach || !probe) return { spoiled: false, reason: "missing sections" };
          const teachText = (teach.innerText || "").toLowerCase();
          // choice buttons in probe
          const choices = Array.from(probe.querySelectorAll('[data-track^="player.choice"], .btn.choice'))
            .map((b) => (b.innerText || "").trim())
            .filter(Boolean);
          const answerHints = [];
          for (const c of choices) {
            if (c.length >= 2 && teachText.includes(c.toLowerCase()) && !/continue|explain|worked/i.test(c)) {
              answerHints.push(c);
            }
          }
          // look for explicit "answer is" patterns in teach while probe visible
          const spoilPhrase = /answer\s+is\b|correct\s+answer\b|the\s+answer[:\s]/i.test(teachText);
          return { spoiled: answerHints.length > 0 || spoilPhrase, answerHints, spoilPhrase, choiceCount: choices.length };
        });
        addCheck(
          "A12c-teach-no-spoil-probe",
          !spoil.spoiled,
          spoil.spoiled ? `Teach appears to leak probe answers: ${JSON.stringify(spoil)}` : `No obvious spoil; choices=${spoil.choiceCount}`,
          "P1"
        );
        if (spoil.spoiled) await shot(page, "fail-A12c-spoil");
      } else {
        note("A12c-skipped", "Teach+probe not both visible on same screen at this step");
      }

      // A12: number-line / arrows readable
      const visualOk = await page.evaluate(() => {
        const lines = Array.from(document.querySelectorAll("svg.number-line, .number-line, svg.visual"));
        const arrows = Array.from(document.querySelectorAll(".box-index, [class*='arrow'], svg"));
        const issues = [];
        for (const svg of lines) {
          const texts = Array.from(svg.querySelectorAll("text"));
          const boxes = texts.map((t) => {
            try {
              const b = t.getBBox();
              return { x: b.x, y: b.y, w: b.width, h: b.height, label: (t.textContent || "").trim() };
            } catch {
              return null;
            }
          }).filter(Boolean);
          for (let i = 0; i < boxes.length; i++) {
            for (let j = i + 1; j < boxes.length; j++) {
              const a = boxes[i], b = boxes[j];
              const overlapX = Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x);
              const overlapY = Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y);
              if (overlapX > a.w * 0.5 && overlapY > a.h * 0.4) {
                issues.push(`overlap:${a.label}|${b.label}`);
              }
            }
          }
        }
        return { lineCount: lines.length, arrowish: arrows.length, issues };
      });
      if (visualOk.lineCount > 0) {
        addCheck(
          "A12-numberline-readable",
          visualOk.issues.length === 0,
          visualOk.issues.length ? `Overlapping labels: ${visualOk.issues.join(",")}` : `number-lines=${visualOk.lineCount} ok`,
          "P2"
        );
        if (visualOk.issues.length) await shot(page, "fail-A12-overlap");
      } else {
        note("A12-numberline", `No number-line SVG on this step (arrowish=${visualOk.arrowish})`);
      }

      // Explain again must change teach content
      const beforeExplain = await teachFingerprint(page);
      const reexplain = page.locator('[data-testid="player.step.regen-reexplain"], [data-track="player.regen.reexplain"]');
      if ((await reexplain.count()) > 0 && beforeExplain.present) {
        const clickedRe = await safeClick(page, reexplain, "Explain again", { waitEnabledTries: 40 });
        if (!clickedRe) {
          addDefect("P1", "regen-explain-again-disabled", "Explain again not clickable", "On teach step click Explain again");
          await shot(page, "fail-explain-again-disabled");
        } else {
        await page.waitForTimeout(2500);
        const afterExplain = await teachFingerprint(page);
        const changed =
          afterExplain.text !== beforeExplain.text ||
          afterExplain.html !== beforeExplain.html ||
          afterExplain.frames !== beforeExplain.frames;
        // also accept variant tag / busy then settle
        const bodyAfter = await bodyText(page);
        const tagged = /variant|re-?explain|another way/i.test(bodyAfter);
        addCheck(
          "regen-explain-again-changes-teach",
          changed || tagged,
          changed
            ? `Teach content changed (textLen ${beforeExplain.text.length}->${afterExplain.text.length})`
            : "Explain again appears to be a no-op (teach fingerprint unchanged)",
          "P0"
        );
        if (!(changed || tagged)) await shot(page, "fail-explain-again-noop");
        else await shot(page, "03-after-explain-again");
        }
      } else {
        note("regen-explain-again", "Explain again control or teach section not present");
      }

      // Worked example must change visible teach/probe content
      const beforeEx = await teachFingerprint(page);
      const bodyBeforeEx = await bodyText(page);
      const exampleBtn = page.locator('[data-testid="player.step.regen-example"], [data-track="player.regen.example"]');
      if ((await exampleBtn.count()) > 0) {
        const clickedEx = await safeClick(page, exampleBtn, "Worked example", { waitEnabledTries: 60 });
        if (!clickedEx) {
          addDefect("P1", "regen-worked-example-stuck-disabled", "Worked example stayed disabled / not clickable", "After Explain again, click Worked example");
          await shot(page, "fail-worked-example-disabled");
        } else {
          await page.waitForTimeout(3500);
          const afterEx = await teachFingerprint(page);
          const bodyAfterEx = await bodyText(page);
          const workedTag = (await page.locator(".worked-example-tag, [data-testid='worked-example'], .worked-example").count()) > 0;
          const changed =
            workedTag ||
            afterEx.text !== beforeEx.text ||
            afterEx.html !== beforeEx.html ||
            bodyAfterEx !== bodyBeforeEx;
          addCheck(
            "regen-worked-example-changes",
            changed,
            changed
              ? `Worked example surfaced (tag=${workedTag})`
              : "Worked example appears to be a no-op",
            "P0"
          );
          if (!changed) await shot(page, "fail-worked-example-noop");
          else await shot(page, "04-after-worked-example");
        }
      } else {
        note("regen-worked-example", "Worked example control not present");
      }

      // Companion: Ask the tutor or force-click floating pet (animating => force)
      let companionOpened = false;
      async function tryOpenCompanion(tag) {
        if ((await page.locator('[data-track="player.tutor"]').count()) > 0) {
          if (await safeClick(page, page.locator('[data-track="player.tutor"]'), tag + "-tutor")) return true;
        }
        const petBtn = page.locator('[aria-label="Open study assistant"], button.pet-button');
        if ((await petBtn.count()) > 0) {
          if (await safeClick(page, petBtn, tag + "-pet", { force: true, waitEnabledTries: 5 })) return true;
          try {
            const box = await petBtn.first().boundingBox();
            if (box) {
              recordControl(tag + "-pet-mouse");
              await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
              await page.waitForTimeout(700);
              if (await page.locator(".companion-panel").isVisible().catch(() => false)) return true;
            }
          } catch (e) {
            recordControl(tag + "-pet-mouse-fail", { error: String(e.message || e) });
          }
        }
        return false;
      }
      companionOpened = await tryOpenCompanion("open-companion");
      if (!companionOpened) {
        const cont = page.locator('[data-testid="player.teach-continue"], [data-track="player.next"]');
        if ((await cont.count()) > 0 && (await cont.first().isEnabled().catch(() => false))) {
          await safeClick(page, cont, "continue-toward-probe");
          await page.waitForTimeout(2500);
          companionOpened = await tryOpenCompanion("open-companion-after-continue");
        }
      }
      await page.waitForTimeout(800);
      const panel = page.locator(".companion-panel");
      if ((await panel.count()) > 0 && (await panel.first().isVisible().catch(() => false))) {
        await shot(page, "05-companion-open");
        const chips = panel.locator(".companion-chips button, [class*='chip']");
        const chipCount = await chips.count();
        note("companion-chips-count", String(chipCount));
        if (chipCount > 0) {
          const beforeChip = await teachFingerprint(page);
          const beforeBody = await bodyText(page);
          recordControl("companion-chip-first", { text: await chips.first().innerText().catch(() => "") });
          await chips.first().click().catch(() => {});
          await page.waitForTimeout(2500);
          const afterChip = await teachFingerprint(page);
          const afterBody = await bodyText(page);
          const chipWorked =
            afterChip.text !== beforeChip.text ||
            afterChip.html !== beforeChip.html ||
            afterBody !== beforeBody ||
            (await page.locator(".worked-example-tag, .variant-tag").count()) > 0;
          addCheck(
            "companion-chips-work",
            chipWorked,
            chipWorked ? "Chip click changed surface" : "Companion chip click looked like a no-op",
            "P1"
          );
          if (!chipWorked) await shot(page, "fail-companion-chip");
        } else {
          addDefect("P1", "companion-chips-work", "Companion open but no chips found", "Open Ask the tutor; expect ActionChip row");
          await shot(page, "fail-companion-no-chips");
        }

        // A13 chat accepts message and shows ack
        const input = panel.locator('input[aria-label="Message"], input[placeholder*="Ask"], textarea');
        const send = panel.locator('[data-track="companion.send"], button[type="submit"]');
        if ((await input.count()) > 0) {
          recordControl("companion-chat-send");
          await input.first().fill("What should I notice on this step?");
          if ((await send.count()) > 0) await send.first().click();
          else await input.first().press("Enter");
          let gotReply = false;
          const start = Date.now();
          while (Date.now() - start < CHAT_TIMEOUT_MS) {
            const bubbles = panel.locator(".companion-bubble.tutor, .companion-bubble.system, .thinking-bubble");
            if ((await bubbles.count()) > 0) {
              // wait past thinking if needed
              const texts = await bubbles.allInnerTexts().catch(() => []);
              if (texts.some((t) => t && t.trim().length > 0 && !/^\.+$/.test(t.trim()))) {
                gotReply = true;
                break;
              }
            }
            await page.waitForTimeout(500);
          }
          addCheck(
            "A13-chat-ack",
            gotReply,
            gotReply ? `Tutor/system ack within ${CHAT_TIMEOUT_MS}ms` : `No chat ack within ${CHAT_TIMEOUT_MS}ms (silent forever?)`,
            "P1"
          );
          if (!gotReply) await shot(page, "fail-A13-chat-silent");
          else await shot(page, "06-chat-ack");
        } else {
          note("A13-chat", "No companion message input found");
        }

        // A14 mic/speaker: companion.mic / companion.speaker (+ player voice.*)
        const voiceBtns = panel.locator('[data-track="companion.mic"], [data-track="companion.speaker"], [data-track="voice.mic"], [data-track="voice.speak"]');
        const voiceCount = await voiceBtns.count();
        if (voiceCount > 0) {
          for (let i = 0; i < Math.min(voiceCount, 4); i++) {
            const btn = voiceBtns.nth(i);
            const label = (await btn.getAttribute("aria-label").catch(() => null)) || (await btn.innerText().catch(() => "")) || "";
            const track = (await btn.getAttribute("data-track").catch(() => null)) || "";
            const clsBefore = await btn.getAttribute("class").catch(() => "");
            recordControl("voice-control", { label, track });
            await btn.click({ force: true }).catch(() => {});
            await page.waitForTimeout(400);
            const clsAfter = await btn.getAttribute("class").catch(() => "");
            const labeled = !!(label && String(label).trim());
            const stateChanged = clsBefore !== clsAfter;
            if (!labeled) {
              addDefect("P2", "A14-voice-unlabeled", "Voice control has no accessible label (" + track + ")", "Inspect companion mic/speaker");
              await shot(page, "fail-A14-unlabeled");
            } else if (!stateChanged) {
              note("A14-voice-maybe-dead", "Clicked [" + label + "] (" + track + ") but no visible class toggle");
            } else {
              note("A14-voice-ok", "Control [" + label + "] (" + track + ") toggled");
            }
          }
        } else {
          note("A14-voice", "No companion/player mic/speaker controls in open panel");
        }
        }

        // close companion
        const collapse = panel.locator('.companion-collapse, [aria-label="Collapse"], button:has-text("Close")');
        if ((await collapse.count()) > 0) await collapse.first().click().catch(() => {});
      } else {
        addDefect("P1", "companion-open", "Could not open companion via Ask the tutor or pet", "On /play click pet (Open study assistant) or Ask the tutor"); await shot(page, "fail-companion-open");
      }

      // Review 1-5 + Submit persists only after Submit
      const reviewPanel = page.locator('[data-testid="player.review.panel"]');
      if ((await reviewPanel.count()) > 0) {
        await shot(page, "07-review-panel");
        const score3 = page.locator('[data-testid="player.review.score-3"]');
        const submit = page.locator('[data-testid="player.review.submit"]');
        const why = page.locator('[data-testid="player.review.why"]');
        if ((await score3.count()) > 0) {
          recordControl("review-score-3");
          await score3.click();
          await page.waitForTimeout(300);
          // before submit, should NOT show submitted receipt
          const submittedBefore = await page.locator('[data-testid="player.review.submitted"]').count();
          addCheck(
            "review-no-persist-before-submit",
            submittedBefore === 0,
            submittedBefore === 0 ? "No submitted receipt before Submit" : "Submitted receipt appeared before Submit",
            "P1"
          );
          if ((await why.count()) > 0) {
            await why.fill("PW defect pass: step was clear enough.");
          }
          const disabled = await submit.isDisabled().catch(() => true);
          if (!disabled) {
            recordControl("review-submit");
            await submit.click();
            await page.waitForTimeout(1500);
            const submittedAfter = await page.locator('[data-testid="player.review.submitted"]').count();
            addCheck(
              "review-persist-after-submit",
              submittedAfter > 0,
              submittedAfter > 0 ? "Submitted receipt visible after Submit" : "No submitted receipt after Submit",
              "P1"
            );
            if (submittedAfter === 0) await shot(page, "fail-review-submit");
            else await shot(page, "08-review-submitted");
          } else {
            // try score then submit
            note("review-submit-disabled", "Submit disabled after score-3; trying score-4");
            await page.locator('[data-testid="player.review.score-4"]').click().catch(() => {});
            await page.waitForTimeout(200);
            if (!(await submit.isDisabled().catch(() => true))) {
              await submit.click();
              await page.waitForTimeout(1500);
              const submittedAfter = await page.locator('[data-testid="player.review.submitted"]').count();
              addCheck("review-persist-after-submit", submittedAfter > 0, `submitted=${submittedAfter}`, "P1");
            } else {
              addDefect("P1", "review-submit", "Submit stayed disabled after rating", "Rate 1-5 then Submit");
            }
          }
        } else {
          note("review-scores", "Review panel present but score buttons missing");
        }
      } else {
        note("review-panel", "Review panel not on this step");
      }

      // A20 Back/exit returns to home/menu
      let exited = false;
      const back = page.locator('[data-track="player.back"]');
      const homeBtn = page.locator('[data-track="player.home"], [data-track="nav.home"], a.brand');
      // Prefer explicit exit/home if in error/done; else brand link
      if ((await page.locator('[data-testid="player-error-home"]').count()) > 0) {
        exited = await safeClick(page, page.locator('[data-testid="player-error-home"]'), "player-error-home");
      } else if ((await homeBtn.count()) > 0) {
        // brand is <a href="/"> 
        exited = await safeClick(page, page.locator("a.brand, [data-track='nav.home']").first(), "nav-home-brand");
      }
      await page.waitForTimeout(1500);
      const url = page.url();
      const onHome =
        /design-bakery\.com\/?$|design-bakery\.com\/try|\/$/.test(url.replace(/https?:\/\//, "")) ||
        url.endsWith("/") ||
        url.includes("/try") ||
        (await page.locator('[data-track="try.start"], [data-track="home.continue"], [data-track="home.lesson.start"]').count()) > 0;
      // If still on play, try browser back? Spec says Back/exit — if missing DEFECT
      if (!onHome) {
        // Look for any Exit / Save and stop
        const exitLink = page.locator('[data-track="lesson.end"], button:has-text("Save and stop"), button:has-text("Exit"), [data-track="player.home"]');
        if ((await exitLink.count()) > 0) {
          await safeClick(page, exitLink, "exit-link");
          await page.waitForTimeout(1500);
        }
      }
      const url2 = page.url();
      const onHome2 =
        !/\/play\//.test(url2) &&
        ((await page.locator('[data-track="try.start"], [data-track="home.continue"], [data-track="home.lesson.start"], .home-lanes, .try-page').count()) > 0 ||
          /\/(try)?\/?$/.test(new URL(url2).pathname));
      addCheck(
        "A20-back-exit-home",
        onHome2,
        onHome2 ? `Returned to menu/home at ${url2}` : `Still on player or no exit path; url=${url2} (Back/exit missing or broken)`,
        "P0"
      );
      if (!onHome2) await shot(page, "fail-A20-no-exit");
      else await shot(page, "09-after-exit-home");

      // If back control exists while in play earlier — note it
      if ((await back.count()) === 0) {
        note("player-back-control", "player.back not shown on sampled step (can_go_back may be false)");
      }
    }

    // Secondary sample: HESI fractions for number-line / arrows (A12)
    try {
      if (!/\/play\//.test(page.url())) {
        await page.goto(BASE + "/", { waitUntil: "domcontentloaded", timeout: NAV_TIMEOUT });
        await page.waitForTimeout(1000);
      }
      // From guest home lanes or try catalog
      let fracStarted = false;
      const fracLane = page.locator(".lesson-item").filter({ hasText: /Comparing fractions|fractions/i }).locator('[data-track="home.lesson.start"], [data-track="try.start"]');
      if ((await fracLane.count()) > 0) fracStarted = await safeClick(page, fracLane, "start-fractions");
      if (!fracStarted) {
        const cont = page.locator('[data-track="home.continue"]').filter({ hasText: /fraction/i });
        if ((await cont.count()) > 0) fracStarted = await safeClick(page, cont, "continue-fractions");
      }
      if (fracStarted) {
        await page.waitForURL(/\/play\//, { timeout: 20000 }).catch(() => {});
        await page.waitForTimeout(2500);
        await shot(page, "10-fractions-step");
        // walk a few Continues looking for number-line
        for (let step = 0; step < 4; step++) {
          const visualOk2 = await page.evaluate(() => {
            const lines = Array.from(document.querySelectorAll("svg.number-line, .number-line, svg.visual"));
            const issues = [];
            for (const svg of lines) {
              const texts = Array.from(svg.querySelectorAll("text"));
              const boxes = texts.map((t) => { try { const b = t.getBBox(); return { x: b.x, y: b.y, w: b.width, h: b.height, label: (t.textContent || "").trim() }; } catch { return null; } }).filter(Boolean);
              for (let i = 0; i < boxes.length; i++) {
                for (let j = i + 1; j < boxes.length; j++) {
                  const a = boxes[i], b = boxes[j];
                  const overlapX = Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x);
                  const overlapY = Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y);
                  if (overlapX > a.w * 0.5 && overlapY > a.h * 0.4) issues.push("overlap:" + a.label + "|" + b.label);
                }
              }
            }
            // BoxIndex arrows
            const arrowLabels = Array.from(document.querySelectorAll(".box-index text, .box-index .label, [class*='box-index'] text"));
            return { lineCount: lines.length, issues, arrowLabelCount: arrowLabels.length, hasFractionBar: !!document.querySelector(".fraction-bar, svg.fraction") };
          });
          if (visualOk2.lineCount > 0) {
            addCheck("A12-numberline-readable", visualOk2.issues.length === 0,
              visualOk2.issues.length ? "Overlapping labels: " + visualOk2.issues.join(",") : "number-lines=" + visualOk2.lineCount + " ok", "P2");
            if (visualOk2.issues.length) await shot(page, "fail-A12-overlap");
            else await shot(page, "11-fractions-numberline");
            break;
          }
          // A14: mic/speaker on probe answer surface
          const voiceBtns2 = page.locator('[data-track="voice.mic"], [data-track="voice.speak"]');
          if ((await voiceBtns2.count()) > 0 && step === 0) {
            for (let vi = 0; vi < Math.min(await voiceBtns2.count(), 2); vi++) {
              const btn = voiceBtns2.nth(vi);
              const label = (await btn.getAttribute("aria-label").catch(() => null)) || (await btn.innerText().catch(() => "")) || "";
              const track = (await btn.getAttribute("data-track").catch(() => null)) || "";
              recordControl("fractions-voice", { label, track });
              const before = await btn.getAttribute("class").catch(() => "");
              await btn.click({ force: true }).catch(() => {});
              await page.waitForTimeout(400);
              const after = await btn.getAttribute("class").catch(() => "");
              if (!String(label).trim() && !track) {
                addDefect("P2", "A14-voice-unlabeled", "Voice control missing label", "Inspect mic/speaker on fractions probe");
                await shot(page, "fail-A14-unlabeled");
              } else {
                note("A14-voice-present", track + " label=" + label + " classChanged=" + (before !== after));
              }
            }
          } else if (step === 0) {
            note("A14-voice-fractions", "No voice.mic/speak on this fractions step yet");
          }
          // A12c on fractions if teach+choices
          if ((await page.locator("section.teach").count()) > 0 && (await page.locator('[data-track^="player.choice"], .btn.choice').count()) > 0) {
            const spoil2 = await page.evaluate(() => {
              const teach = document.querySelector("section.teach");
              const probe = document.querySelector("section.probe");
              if (!teach || !probe) return { spoiled: false };
              const teachText = (teach.innerText || "").toLowerCase();
              const choices = Array.from(probe.querySelectorAll('[data-track^="player.choice"], .btn.choice')).map(b => (b.innerText||"").trim()).filter(Boolean);
              const hits = choices.filter(c => c.length >= 2 && teachText.includes(c.toLowerCase()));
              // spoiling = teach states the correct answer explicitly, not merely naming both fractions
              const spoilPhrase = /answer\s+is\b|correct\s+answer\b|bigger\s+is\b|therefore\s+[0-9]/i.test(teachText);
              return { spoiled: spoilPhrase, hits, choiceCount: choices.length };
            });
            addCheck("A12c-fractions-teach-no-spoil", !spoil2.spoiled,
              spoil2.spoiled ? JSON.stringify(spoil2) : "No explicit answer spoiler on fractions teach+probe", "P1");
          }
          note("A12-fractions-step-" + step, "lines=" + visualOk2.lineCount + " arrows=" + visualOk2.arrowLabelCount + " fracBar=" + visualOk2.hasFractionBar);
          const cont2 = page.locator('[data-testid="player.teach-continue"], [data-track="player.next"]');
          if ((await cont2.count()) === 0) break;
          const okc = await safeClick(page, cont2, "fractions-continue-" + step);
          if (!okc) break;
          await page.waitForTimeout(2000);
        }
      } else {
        note("A12-fractions", "Could not start fractions lesson for number-line sample");
      }
    } catch (e) {
      note("A12-fractions-error", String(e && e.message ? e.message : e));
    }

    // Capture console errors as soft notes
    if (consoleErrors.length) {
      note("console-errors", consoleErrors.slice(0, 10).join(" | "));
    }
  } catch (e) {
    addDefect("P0", "suite-crash", `${e && e.stack ? e.stack : e}`, "Re-run defect pass");
    try {
      await shot(page, "fail-suite-crash");
    } catch {}
  }

  await browser.close();

  // Dedupe defects by id keeping highest severity
  const sevRank = { P0: 0, P1: 1, P2: 2, info: 9 };
  const byId = new Map();
  for (const d of defects) {
    const prev = byId.get(d.id);
    if (!prev || (sevRank[d.severity] ?? 9) < (sevRank[prev.severity] ?? 9)) byId.set(d.id, d);
  }
  const unique = [...byId.values()];
  const p0 = unique.filter((d) => d.severity === "P0");
  const p1 = unique.filter((d) => d.severity === "P1");
  const p2 = unique.filter((d) => d.severity === "P2");

  const summary = {
    base_url: BASE,
    started_at: process.env.RUN_STARTED || utcNow(),
    finished_at: utcNow(),
    artifact_dir: ART,
    counts: {
      checks: checks.length,
      defects: unique.length,
      P0: p0.length,
      P1: p1.length,
      P2: p2.length,
      controls_tried: controlsTried.length,
      passes: checks.filter((c) => c.ok).length,
      fails: checks.filter((c) => !c.ok).length,
    },
    defects: unique,
    checks,
    controls_tried: controlsTried,
  };

  fs.writeFileSync(path.join(ART, "summary.json"), JSON.stringify(summary, null, 2));

  const md = [];
  md.push(`# Study OS Playwright UX defect pass`);
  md.push("");
  md.push(`- Base URL: ${BASE}`);
  md.push(`- Finished: ${summary.finished_at}`);
  md.push(`- Guest: yes`);
  md.push(`- Checks: ${summary.counts.checks} (pass ${summary.counts.passes} / fail ${summary.counts.fails})`);
  md.push(`- Defects: **${summary.counts.defects}** (P0=${summary.counts.P0}, P1=${summary.counts.P1}, P2=${summary.counts.P2})`);
  md.push(`- Controls tried: ${summary.counts.controls_tried}`);
  md.push("");
  md.push(`## Defects P0`);
  if (!p0.length) md.push("_None_");
  for (const d of p0) {
    md.push(`### ${d.id}`);
    md.push(`- Detail: ${d.detail}`);
    md.push(`- Repro: ${d.repro || "See Method in task brief; screenshots/ in this artifact dir"}`);
    md.push("");
  }
  md.push(`## Defects P1`);
  if (!p1.length) md.push("_None_");
  for (const d of p1) {
    md.push(`### ${d.id}`);
    md.push(`- Detail: ${d.detail}`);
    md.push(`- Repro: ${d.repro || "See screenshots/"}`);
    md.push("");
  }
  md.push(`## Defects P2`);
  if (!p2.length) md.push("_None_");
  for (const d of p2) {
    md.push(`### ${d.id}`);
    md.push(`- Detail: ${d.detail}`);
    md.push(`- Repro: ${d.repro || "See screenshots/"}`);
    md.push("");
  }
  md.push(`## Controls tried`);
  for (const c of controlsTried) {
    md.push(`- \`${c.t}\` **${c.name}** ${c.action || ""} ${c.error ? "ERR " + c.error : ""}`);
  }
  md.push("");
  md.push(`## All checks`);
  for (const c of checks) {
    md.push(`- ${c.ok ? "PASS" : "FAIL"} [${c.severity}] ${c.id}: ${c.detail}`);
  }
  fs.writeFileSync(path.join(ART, "report.md"), md.join("\n"));
  console.log("\n=== SUMMARY ===");
  console.log(JSON.stringify(summary.counts, null, 2));
  console.log("Artifacts:", ART);
}

run().catch((e) => {
  console.error(e);
  process.exit(2);
});

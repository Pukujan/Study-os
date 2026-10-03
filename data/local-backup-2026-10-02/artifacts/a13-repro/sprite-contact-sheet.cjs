/**
 * SOS-0014: contact sheet of every walk/turn frame as the app actually crops it.
 *
 * Clones the live sprite element and steps background-position through the same
 * formula Sprite uses (col = f % cols, row = floor(f / cols), cell = rendered
 * w/h), so this proves the sheet divides cleanly into N distinct frames with no
 * bleed from a neighbouring cell.
 *
 * Usage: node sprite-contact-sheet.cjs [baseUrl]
 */
const { chromium } = require("../../web/node_modules/playwright");
const fs = require("fs");
const path = require("path");

const BASE = process.argv[2] || "http://127.0.0.1:4173";
const OUT = path.join(__dirname, "contact-sheets");

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  await page.goto(BASE, { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.locator('[data-track="try.start"]').first().click({ timeout: 30000 });
  await page.waitForURL(/\/play\//, { timeout: 30000 });
  await page.waitForTimeout(2000);
  await page.locator("[data-pet-float]").waitFor({ state: "visible", timeout: 20000 });

  for (const sheet of [
    { name: "walk", src: "/mascot/pet-walk.webp", frames: 6, cols: 3 },
    { name: "turn", src: "/mascot/pet-turn.webp", frames: 4, cols: 2 },
  ]) {
    const grid = await page.evaluate(
      ({ src, frames, cols }) => {
        const host = document.querySelector("[data-pet-float]");
        const sprite = host.querySelector(".pet-sprite");
        const cs = getComputedStyle(sprite);
        const w = parseFloat(cs.width);
        const h = parseFloat(cs.height);
        const rows = Math.ceil(frames / cols);
        const sheetW = cols * w;
        const sheetH = rows * h;
        const out = [];
        for (let f = 0; f < frames; f++) {
          const col = f % cols;
          const row = Math.floor(f / cols);
          out.push({ f, col, row, x: -col * w, y: -row * h });
        }
        return { w, h, cols, rows, sheetW, sheetH, frames: out };
      },
      { src: sheet.src, frames: sheet.frames, cols: sheet.cols },
    );

    const cellW = Math.round(grid.w);
    const cellH = Math.round(grid.h);
    const html = `<!doctype html><body style="margin:0;background:#111;display:flex;flex-wrap:wrap;gap:8px;padding:8px;width:${grid.cols * (cellW + 8) + 16}px">
      ${grid.frames
        .map(
          (fr) => `<div style="position:relative">
        <div style="width:${cellW}px;height:${cellH}px;background-image:url('${BASE}${sheet.src}');
          background-repeat:no-repeat;background-size:${grid.sheetW}px ${grid.sheetH}px;
          background-position:${fr.x}px ${fr.y}px;outline:1px solid #444"></div>
        <div style="color:#9ae;font:11px monospace;text-align:center">f${fr.f} c${fr.col} r${fr.row}</div>
      </div>`,
        )
        .join("")}
    </body>`;

    const p2 = await browser.newPage({ viewport: { width: grid.cols * (cellW + 8) + 40, height: 400 } });
    await p2.setContent(html);
    await p2.waitForTimeout(600);
    await p2.screenshot({ path: path.join(OUT, `${sheet.name}.png`), fullPage: true });
    console.log(`${sheet.name}: cell=${cellW}x${cellH} sheet=${grid.sheetW}x${grid.sheetH} rows=${grid.rows} -> contact-sheets/${sheet.name}.png`);
    await p2.close();
  }

  await browser.close();
})();

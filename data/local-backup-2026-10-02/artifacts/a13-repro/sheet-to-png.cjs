/**
 * Render a sprite sheet to PNG so a human/agent can actually look at it.
 * Scratch tooling for SOS-0014 review; not part of the product.
 *
 * Usage: node sheet-to-png.cjs <sheetPath> <outPng> [scale]
 */
const { chromium } = require("../../web/node_modules/playwright");
const path = require("path");
const fs = require("fs");

const sheet = process.argv[2];
const out = process.argv[3];
const scale = Number(process.argv[4] || 2);

(async () => {
  const abs = path.resolve(sheet);
  const b64 = fs.readFileSync(abs).toString("base64");
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1200, height: 800 } });
  await page.setContent(
    `<body style="margin:0;background:#222">
       <img id="s" src="data:image/webp;base64,${b64}" style="image-rendering:pixelated;transform:scale(${scale});transform-origin:top left">
     </body>`,
  );
  const el = page.locator("#s");
  await el.waitFor({ state: "visible" });
  await el.screenshot({ path: out, omitBackground: false });
  const box = await el.boundingBox();
  console.log(`${path.basename(sheet)} -> ${out} (natural ${box.width / scale}x${box.height / scale})`);
  await browser.close();
})();

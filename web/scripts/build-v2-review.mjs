/**
 * Produce exactly one HTML file that can be opened via file://, without a
 * development server, model keys or production DB. Strictly reject leftover
 * network/source asset dependencies. Refs #204.
 */
import { execFileSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const web = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const out = resolve(web, "dist-review");
execFileSync("npx", ["vite", "build", "--config", "vite.review.config.ts"], { cwd: web, stdio: "inherit" });

let html = readFileSync(resolve(out, "v2-review.html"), "utf8");
let modules = 0;
let styles = 0;

function resolveBundledPath(src) {
  if (/^(https?:|data:|\/\/)/i.test(src)) throw new Error("External preview dependency: " + src);
  const target = resolve(out, src.replace(/^\.\//, ""));
  if (!target.startsWith(out + sep)) throw new Error("Preview asset escapes build directory: " + src);
  return readFileSync(target, "utf8");
}

// Vite's static single-entry output has one JS module and one CSS asset.
html = html.replace(/<script\b([^>]*)><\/script>/g, (tag, attrs) => {
  const source = /\bsrc="([^"]+)"/.exec(attrs);
  if (!source) return tag;
  if (!/\btype="module"/.test(attrs)) throw new Error("Unexpected executable script: " + tag);
  modules += 1;
  const js = resolveBundledPath(source[1]);
  if (/<\/script/i.test(js)) throw new Error("Unsafe raw </script> in built JavaScript");
  return "<script type=\"module\">" + js + "</script>";
});
html = html.replace(/<link\b([^>]+)>/g, (tag, attrs) => {
  if (/\brel="modulepreload"/.test(attrs)) throw new Error("Unexpected preview modulepreload chunk");
  if (!/\brel="stylesheet"/.test(attrs)) return tag;
  const href = /\bhref="([^"]+)"/.exec(attrs);
  if (!href) throw new Error("Missing stylesheet href");
  styles += 1;
  const css = resolveBundledPath(href[1]);
  if (/<\/style/i.test(css)) throw new Error("Unsafe raw </style> in built CSS");
  return "<style>" + css + "</style>";
});
if (modules !== 1 || styles !== 1) {
  throw new Error(`Expected exactly one inline module and CSS bundle, found ${modules} and ${styles}`);
}
if (/<(?:script|link)\b[^>]+(?:src|href)="(?:\.\/|\/|https?:)/.test(html)) {
  throw new Error("Preview still depends on an external asset");
}
const sha = process.env.GITHUB_SHA || "local-unversioned";
html = html.replace("</head>", `<meta name="study-os-review-commit" content="${sha.replace(/[^a-f0-9-]/g, "")}"></head>`);
const target = resolve(out, "review.html");
writeFileSync(target, html, "utf8");
console.log(`Created offline interactive review: ${target} (${(Buffer.byteLength(html) / 1024).toFixed(1)} KiB)`);

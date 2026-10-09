/**
 * Offline-only PR reviewer. No API, auth, analytics, learner persistence,
 * model provider, or production route. This becomes one self-contained HTML.
 * Refs #204 / PR #205.
 */
import { createRoot } from "react-dom/client";
import "../theme/tokens.css";
import "./review.css";
import BigOStudio from "./BigOStudio";

const root = document.getElementById("review-root");
if (!root) throw new Error("Missing preview container");
createRoot(root).render(
  <>
    <header className="v2-review-banner" role="note">
      <strong>Study OS v2 · unmerged prototype</strong>
      <span>Offline review copy — no login, learner data, AI calls or production changes</span>
    </header>
    <main className="shell shell-v2">
      <BigOStudio onExit={() => { window.location.assign("https://study.design-bakery.com/"); }} />
    </main>
    <footer className="v2-review-footer">
      Prototype only. Check definitions, equation ↔ graph ↔ game consistency, mobile layout,
      and whether the explanation actually helps a beginner understand the concept.
    </footer>
  </>,
);

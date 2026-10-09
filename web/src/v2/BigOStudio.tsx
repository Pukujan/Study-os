import { useId, useState, type FormEvent } from "react";
import { navigate } from "../router";
import SticksBoxesComplexity, { type ComplexityMode } from "../visuals/SticksBoxesComplexity";
import { BIG_O_RULES, BIG_O_TERMS, challengeSize, curvePoints, exactEquation, exampleWork } from "./bigOModel";
import styles from "./BigOStudio.module.css";

const MODES: ComplexityMode[] = ["O(1)", "O(n)", "O(n²)"];
const SERIES_COLORS: Record<ComplexityMode, string> = {
  "O(1)": "var(--chart-1, #22a7a7)",
  "O(n)": "var(--chart-2, #688bea)",
  "O(n²)": "var(--chart-4, #df9b42)",
};

function BigOGraph({ mode, n }: { mode: ComplexityMode; n: number }) {
  const titleId = useId();
  const descId = useId();
  const x = (size: number) => 44 + (size - 1) * 60;
  const y = (work: number) => 220 - (work / 64) * 172;
  const current = exampleWork(mode, n);

  return (
    <figure className={styles.graph} aria-label="Work growth graph">
      <svg
        viewBox="0 0 510 270"
        role="img"
        aria-labelledby={`${titleId} ${descId}`}
        data-testid="v2-curve"
      >
        <title id={titleId}>Illustrative work by input size</title>
        <desc id={descId}>
          O(1) stays at 1, O(n) rises with n and O(n²) rises with n squared.
          Selected {mode} at n={n} has {current} placements in this game.
        </desc>
        {[0, 16, 32, 48, 64].map((work) => (
          <g key={work}>
            <line x1="44" x2="464" y1={y(work)} y2={y(work)} stroke="currentColor" opacity=".15" />
            <text x="37" y={y(work) + 4} textAnchor="end" fontSize="11" fill="currentColor">{work}</text>
          </g>
        ))}
        <line x1="44" y1="220" x2="480" y2="220" stroke="currentColor" opacity=".55" />
        <line x1="44" y1="220" x2="44" y2="34" stroke="currentColor" opacity=".55" />
        {Array.from({ length: 8 }, (_, i) => i + 1).map((size) => (
          <text key={size} x={x(size)} y="237" textAnchor="middle" fontSize="11" fill="currentColor">{size}</text>
        ))}
        <text x="250" y="258" textAnchor="middle" fontSize="12" fill="currentColor">n — number of boxes</text>
        <text x="44" y="17" fontSize="12" fill="currentColor">W(n) — placements</text>
        {MODES.map((candidate) => (
          <polyline
            key={candidate}
            points={curvePoints(candidate).map((point) => `${x(point.n)},${y(point.work)}`).join(" ")}
            fill="none"
            stroke={SERIES_COLORS[candidate]}
            strokeWidth={candidate === mode ? 4 : 2}
            opacity={candidate === mode ? 1 : 0.38}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        ))}
        <line x1={x(n)} y1="34" x2={x(n)} y2="220" stroke="currentColor" opacity=".25" strokeDasharray="4 4" />
        <circle cx={x(n)} cy={y(current)} r="7" stroke="var(--card)" strokeWidth="2" fill={SERIES_COLORS[mode]} />
      </svg>
      <figcaption className={styles.graphCaption}>
        {MODES.map((candidate) => (
          <span key={candidate} className={candidate === mode ? styles.activeLegend : styles.legend}>
            <span className={styles.legendDot} style={{ background: SERIES_COLORS[candidate] }} aria-hidden="true" />
            {candidate}
          </span>
        ))}
      </figcaption>
      <p className={styles.graphNote}>Selected: {mode} at n = {n}, so W(n) = {current} placements.</p>
    </figure>
  );
}

/**
 * An isolated, guest-safe experience proof. No API writes, model generation or
 * mastery claim. The route is disabled unless VITE_STUDY_OS_V2=1 at build time.
 * Refs #204. Keep the legacy player intact until journey+golden gates pass.
 */
export default function BigOStudio() {
  const [started, setStarted] = useState(false);
  const [mode, setMode] = useState<ComplexityMode>("O(n)");
  const [n, setN] = useState(3);
  const [placed, setPlaced] = useState(0);
  const [prediction, setPrediction] = useState("");
  const [checked, setChecked] = useState(false);
  const total = exampleWork(mode, n);
  const nextN = challengeSize(n);
  const expected = exampleWork(mode, nextN);
  const isValidAnswer = /^\d+$/.test(prediction.trim());
  const isCorrect = checked && Number(prediction) === expected;

  function changeExample(nextMode: ComplexityMode, nextN: number) {
    setMode(nextMode);
    setN(nextN);
    setPlaced(0);
    setPrediction("");
    setChecked(false);
  }

  function checkPrediction(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isValidAnswer) setChecked(true);
  }

  if (!started) {
    return (
      <div className={styles.root} data-testid="v2-welcome">
        <div className={styles.hero}>
          <span className={styles.eyebrow}>Study OS v2 / preview</span>
          <h1>Understand Big O by doing</h1>
          <p>Before formulas or quizzes, try a tiny game. See what the boxes, equation and graph are showing you.</p>
          <p className={styles.small}>No account needed. This is a sandbox preview; no learning progress is saved or graded.</p>
          <div className={styles.heroActions}>
            <button type="button" className={styles.primary} onClick={() => setStarted(true)} data-testid="v2-start">
              Start with three boxes
            </button>
            <button type="button" className={styles.secondary} onClick={() => navigate("/")}>Return to Study OS</button>
          </div>
        </div>
        <section className={styles.overview} aria-label="What you will learn">
          <h2>First, what do these symbols mean?</h2>
          <dl className={styles.glossary}>
            {BIG_O_TERMS.map((term) => (
              <div key={term.symbol}><dt>{term.symbol}</dt><dd>{term.definition}</dd></div>
            ))}
          </dl>
        </section>
      </div>
    );
  }

  return (
    <div className={styles.root} data-testid="v2-studio">
      <nav className={styles.navigation} aria-label="Learning preview navigation">
        <button type="button" className={styles.back} data-testid="v2-back" onClick={() => setStarted(false)}>
          ← Overview
        </button>
        <span>Big O · Explore</span>
        <button type="button" className={styles.back} onClick={() => navigate("/")}>Study OS home</button>
      </nav>
      <header className={styles.intro}>
        <span className={styles.eyebrow}>One idea at a time</span>
        <h1>How does work change when a problem gets bigger?</h1>
        <p>Each box is one input item. You are the computer: place sticks to count the work a rule requires.</p>
      </header>
      <div className={styles.columns}>
        <section className={styles.gamePanel} aria-label="Interactive example">
          <div className={styles.heading}>
            <span className={styles.number}>01</span>
            <div><h2>Try the rule</h2><p>{BIG_O_RULES[mode].action}</p></div>
          </div>
          <div className={styles.gameArea}>
            <SticksBoxesComplexity
              frame={{ type: "sticks_boxes_complexity", initial_complexity: mode, initial_n: n, n_min: 2, n_max: 8 }}
              onChange={changeExample}
              onProgress={setPlaced}
            />
          </div>
          <p className={styles.progress} data-testid="v2-progress" aria-live="polite">
            {placed} of {total} stick placements completed. {placed === total ? "You completed this example." : "Put in the next stick to see the count change."}
          </p>
        </section>

        <section className={styles.explainPanel} aria-label="Meaning of the example">
          <div className={styles.heading}>
            <span className={styles.number}>02</span>
            <div><h2>Connect the meaning</h2><p>{BIG_O_RULES[mode].pattern}</p></div>
          </div>
          <dl className={styles.glossary}>
            {BIG_O_TERMS.map((term) => (
              <div key={term.symbol}>
                <dt>{term.symbol}</dt>
                <dd>{term.definition}</dd>
              </div>
            ))}
          </dl>
          <div className={styles.equation}>
            <span>For the selected boxes and rule</span>
            <strong data-testid="v2-equation">{exactEquation(mode, n)}</strong>
            <p>This is the game's <em>exact count</em>. Big O describes a growth family, not exact runtime.</p>
          </div>
          <BigOGraph mode={mode} n={n} />
        </section>
      </div>
      <section className={styles.practice} aria-label="Predict without placing sticks">
        <div className={styles.heading}>
          <span className={styles.number}>03</span>
          <div><h2>Now predict</h2><p>Keep the {mode} rule, but imagine {nextN} boxes. How many placements would that take?</p></div>
        </div>
        <form className={styles.answerForm} onSubmit={checkPrediction}>
          <label htmlFor="v2-prediction">Your prediction (a whole number)</label>
          <div className={styles.answerRow}>
            <input
              id="v2-prediction"
              type="number"
              inputMode="numeric"
              min="0"
              step="1"
              value={prediction}
              onChange={(event) => { setPrediction(event.target.value); setChecked(false); }}
              aria-label="Number of stick placements"
            />
            <button type="submit" className={styles.primary} data-testid="v2-check" disabled={!isValidAnswer}>Check answer</button>
          </div>
        </form>
        {checked && (
          <p role="status" data-testid="v2-result" className={styles.result}>
            {isCorrect
              ? `Yes. ${exactEquation(mode, nextN)}. You applied the same rule to a new input size.`
              : `Not quite. For ${nextN} boxes, the rule gives ${exactEquation(mode, nextN)}. Try another size in the game and compare.`}
          </p>
        )}
      </section>
      <p className={styles.footnote}>Preview only: all displayed counts come from the original sticks-and-boxes game rule. No generative model supplies equations or assessment answers.</p>
    </div>
  );
}

import { useId, useState } from "react";
import { navigate } from "../router";
import GrowthGame from "./GrowthGame";
import { BIG_O_TERMS, exactEquation, exampleWork } from "./bigOModel";
import { GROWTH_MISSIONS } from "./growthMission";
import type { ComplexityMode } from "../visuals/SticksBoxesComplexity";
import styles from "./BigOStudio.module.css";

type Measurement = { id: string; mode: ComplexityMode; n: number; work: number };
const COLORS: Record<ComplexityMode, string> = {
  "O(1)": "#86e4cc",
  "O(n)": "#8eb4ff",
  "O(n²)": "#ffbf78",
};

/**
 * Shows the number of accepted operations live. Until the board is finished,
 * the animated bar is only *partial work*, not a measured complexity sample.
 * Completed runs alone enter the observed curve. Never plot a fake oracle
 * answer ahead of a learner's independent action.
 */
function LiveGrowthGraph({
  n, count, finished, history,
}: { n: number; count: number; finished: boolean; history: readonly Measurement[] }) {
  const titleId = useId();
  const descId = useId();
  const x = (size: number) => 68 + (size - 1) * 97;
  const y = (work: number) => 238 - (work / 16) * 190;
  const all: Measurement[] = [...history];
  const byMode = (mode: ComplexityMode) => all.filter((sample) => sample.mode === mode)
    .sort((a, b) => a.n - b.n);
  const modes: ComplexityMode[] = ["O(1)", "O(n)", "O(n²)"];

  return (
    <figure className={styles.graph}>
      <svg viewBox="0 0 505 300" role="img" aria-labelledby={`${titleId} ${descId}`}
        data-testid="v2-curve" data-live-work={count} data-current-n={n}>
        <title id={titleId}>Growth of work observed in the game</title>
        <desc id={descId}>The current board uses {n} boxes and has {count} valid placements.
          Previous points represent completed boards only; this bar is
          {finished ? " finished" : " still growing"}.</desc>
        {[0, 4, 8, 12, 16].map((steps) => (
          <g key={steps}>
            <line x1="60" y1={y(steps)} x2="478" y2={y(steps)} stroke="currentColor" opacity=".16" />
            <text x="52" y={y(steps) + 4} textAnchor="end" fill="currentColor" fontSize="13">{steps}</text>
          </g>
        ))}
        <line x1="60" y1="238" x2="478" y2="238" stroke="currentColor" opacity=".5" />
        <line x1="60" y1="238" x2="60" y2="42" stroke="currentColor" opacity=".5" />
        {[2, 3, 4].map((size) => (
          <text key={size} x={x(size)} y="257" textAnchor="middle" fill="currentColor" fontSize="13">
            {size}
          </text>
        ))}
        <text x="266" y="286" textAnchor="middle" fill="currentColor" fontSize="13">
          n — boxes in the task
        </text>
        <text x="63" y="22" fill="currentColor" fontSize="13">Work — sticks placed</text>
        {modes.map((mode) => {
          const points = byMode(mode);
          return points.length >= 2 ? (
            <polyline key={mode}
              points={points.map((p) => `${x(p.n)},${y(p.work)}`).join(" ")}
              fill="none" stroke={COLORS[mode]} strokeWidth="2.5" />
          ) : null;
        })}
        {history.map((p) => (
          <circle key={p.id} cx={x(p.n)} cy={y(p.work)} r="6" fill={COLORS[p.mode]}
            stroke="var(--card)" strokeWidth="2" />
        ))}
        <rect data-testid="v2-live-bar" x={x(n) - 15} width="30"
          y={y(count)} height={Math.max(0, y(0) - y(count))} rx="5"
          fill={COLORS["O(n²)"]} opacity=".64" />
        <circle cx={x(n)} cy={y(count)} r="7" fill={COLORS["O(n²)"]}
          stroke="var(--card)" strokeWidth="2" />
      </svg>
      <figcaption className={styles.graphCaption} data-testid="v2-graph-caption" aria-live="polite">
        <strong>{count} work step{count === 1 ? "" : "s"} so far</strong> with {n} boxes.
        {finished ? " This board is complete." : " This board is still in progress."}
      </figcaption>
      {history.length ? (
        <div className={styles.legend} aria-label="Completed example measurements">
          {modes.filter((mode) => byMode(mode).length > 0).map((mode) => (
            <span key={mode}><i style={{ background: COLORS[mode] }} /> Completed {mode} examples</span>
          ))}
        </div>
      ) : null}
    </figure>
  );
}

/** Entire v2 lives at /v2. No API writes, accounts, model calls or mastery claims. */
export default function BigOStudio({ onExit = () => navigate("/") }: { onExit?: () => void } = {}) {
  const [started, setStarted] = useState(false);
  const [missionIndex, setMissionIndex] = useState(0);
  const [count, setCount] = useState(0);
  const [filledKeys, setFilledKeys] = useState<string[]>([]);
  const [finished, setFinished] = useState(false);
  const [history, setHistory] = useState<Measurement[]>([]);
  const mission = GROWTH_MISSIONS[missionIndex];
  const isLast = missionIndex === GROWTH_MISSIONS.length - 1;

  function nextMission() {
    if (!finished) return;
    const measured: Measurement = {
      id: mission.id, mode: mission.mode, n: mission.n,
      work: exampleWork(mission.mode, mission.n),
    };
    if (!history.some((existing) => existing.id === mission.id)) {
      setHistory([...history, measured]);
    }
    if (!isLast) {
      setMissionIndex(missionIndex + 1);
      setCount(0);
      setFilledKeys([]);
      setFinished(false);
    }
  }

  if (!started) return (
    <div className={styles.root} data-testid="v2-welcome">
      <section className={styles.hero}>
        <span className={styles.eyebrow}>Study OS v2 · live game preview</span>
        <h1>Don't pick a formula. Discover it.</h1>
        <p>The computer gives you a job. You drag sticks onto boxes or pairs of boxes. The graph grows with every correct move. The game checks your work immediately.</p>
        <p className={styles.muted}>No account needed. This preview does not save results or claim mastery.</p>
        <div className={styles.actions}>
          <button type="button" data-testid="v2-start" className={styles.primary}
            onClick={() => setStarted(true)}>Play the first mission</button>
          <button type="button" className={styles.secondary} onClick={onExit}>Study OS home</button>
        </div>
      </section>
      <section className={styles.overview}>
        <h2>Just three pieces of language to start</h2>
        <dl className={styles.glossary}>
          {BIG_O_TERMS.map((term) => <div key={term.symbol}><dt>{term.symbol}</dt><dd>{term.definition}</dd></div>)}
        </dl>
        <p className={styles.muted}>You won't need to pick O(1), O(n), or O(n²). Those are names we'll attach after you've played.</p>
      </section>
    </div>
  );

  return (
    <div className={styles.root} data-testid="v2-studio">
      <nav className={styles.navigation} aria-label="Preview navigation">
        <button className={styles.secondary} type="button" data-testid="v2-back"
          onClick={() => setStarted(false)}>← Overview</button>
        <span>Mission {missionIndex + 1} of {GROWTH_MISSIONS.length}</span>
        <button className={styles.secondary} type="button" onClick={onExit}>Study OS home</button>
      </nav>
      <header className={styles.intro}>
        <span className={styles.eyebrow}>The computer's task · {mission.n} boxes</span>
        <h1>{mission.heading}</h1>
        <p>{mission.instruction}</p>
      </header>
      <div className={styles.columns}>
        <section className={styles.gamePanel} aria-label="Live game board">
          <div className={styles.heading}><span className={styles.number}>01</span><div>
            <h2>Do the job</h2>
            <p>Drag the stick to a tile, or tap the stick then tap a tile. The game checks each move.</p>
          </div></div>
          <GrowthGame key={mission.id} mission={mission} initialFilled={filledKeys}
            onProgress={(keys, done) => { setFilledKeys(keys); setCount(keys.length); setFinished(done); }} />
        </section>
        <section className={styles.explainPanel} aria-label="Live work graph">
          <div className={styles.heading}><span className={styles.number}>02</span><div>
            <h2>Watch the graph grow</h2>
            <p>Every valid placement is one work step. Only finished boards count as complete measurements.</p>
          </div></div>
          <LiveGrowthGraph n={mission.n} count={count} finished={finished} history={history} />
          {finished ? (
            <div className={styles.reveal} data-testid="v2-rule-reveal" role="status">
              <span>The pattern you just made has a name</span>
              <strong>{mission.mode}</strong>
              <p data-testid="v2-equation">{exactEquation(mission.mode, mission.n)}</p>
              <p>Here W(n) means the exact number of sticks placed in <em>this game</em>. Big O names the way a pattern grows, not the exact runtime of all programs.</p>
            </div>
          ) : (
            <p className={styles.muted} data-testid="v2-rule-hidden">
              The growth label and complete equation will appear after you finish the task. For now, watch your work counter.
            </p>
          )}
        </section>
      </div>
      <section className={styles.nextPanel}>
        <div>
          <h2>{finished ? "Good work—your board was checked as you played." : "The board is your answer."}</h2>
          <p data-testid="v2-progress">
            {finished ? `You completed ${count} valid placements. The graph and equation now match the board.`
              : `${count} valid placement${count === 1 ? "" : "s"} so far. Keep filling the required spaces.`}
          </p>
        </div>
        {finished && !isLast ? (
          <button type="button" className={styles.primary} data-testid="v2-next"
            onClick={nextMission}>Let the computer choose the next job →</button>
        ) : finished && isLast ? (
          <p role="status" data-testid="v2-finished-all">You've played every rule! These are observed game examples, not a claim that you've mastered Big O.</p>
        ) : null}
      </section>
    </div>
  );
}

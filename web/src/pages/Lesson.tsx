import { useEffect, useRef, useState, type FormEvent } from "react";
import { api, ApiError, newIdempotencyKey, type Turn } from "../api";
import { Markdown, stripChoiceList } from "../markdown";
import { navigate } from "../router";
import { tracker } from "../tracker";

const HINT_LABEL: Record<string, string> = {
  repeat_representation: "Show the picture again",
  worked_example: "Show a worked example",
  simpler_example: "Try a simpler example",
  why: "Why?",
};

const REACTIONS: [string, string][] = [
  ["helped", "That helped"],
  ["confused", "I’m confused"],
  ["too_easy", "Too easy"],
];

export default function Lesson({ sessionId }: { sessionId: string }) {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reacted, setReacted] = useState<Record<string, string>>({});
  const pendingKey = useRef<{ turn: string; key: string } | null>(null);
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.session(sessionId).then((v) => setTurns(v.turns)).catch((e) => setError(e instanceof ApiError ? e.code : "error"));
    return () => tracker.endStep();
  }, [sessionId]);

  const last = turns[turns.length - 1];
  const awaiting = last && last.state === "AWAIT_ATTEMPT" ? [...turns].reverse().find((t) => t.awaiting) : undefined;
  const done = last && (last.state === "SESSION_DONE" || last.state === "PAUSED");

  useEffect(() => {
    if (awaiting) tracker.stepShown(sessionId, awaiting.turn_id, awaiting.step_id);
    bottom.current?.scrollIntoView?.({ behavior: "smooth", block: "end" });
  }, [awaiting?.turn_id, sessionId]); // eslint-disable-line react-hooks/exhaustive-deps

  const append = (more: Turn[]) => setTurns((prev) => {
    const seen = new Set(prev.map((t) => t.turn_id));
    return [...prev, ...more.filter((t) => !seen.has(t.turn_id))];
  });

  const submit = async (response: string) => {
    if (!awaiting || busy || !response.trim()) return;
    setBusy(true);
    setError(null);
    if (!pendingKey.current || pendingKey.current.turn !== awaiting.turn_id) {
      pendingKey.current = { turn: awaiting.turn_id, key: newIdempotencyKey() };
    }
    const ms = tracker.stepAnswered();
    try {
      const res = await api.attempt(sessionId, awaiting.turn_id, response, pendingKey.current.key, ms);
      pendingKey.current = null;
      setAnswer("");
      append(res.turns);
    } catch (e) {
      setError(e instanceof ApiError ? e.code : "network");
      tracker.stepShown(sessionId, awaiting.turn_id, awaiting.step_id);
    } finally {
      setBusy(false);
    }
  };

  const hint = async (kind: string) => {
    if (!awaiting) return;
    setBusy(true);
    tracker.hint(kind);
    try {
      append((await api.expand(sessionId, awaiting.turn_id, kind)).turns);
    } catch (e) {
      setError(e instanceof ApiError ? e.code : "network");
    } finally {
      setBusy(false);
    }
  };

  const react = async (turnId: string, kind: string) => {
    setReacted((r) => ({ ...r, [turnId]: kind }));
    tracker.track({ type: "rating", control: kind, turn_id: turnId, session_id: sessionId });
    await api.react(turnId, kind).catch(() => undefined);
  };

  const end = async () => {
    setBusy(true);
    await api.end(sessionId).catch(() => undefined);
    navigate(`/summary/${sessionId}`);
  };

  const onForm = (e: FormEvent) => {
    e.preventDefault();
    void submit(answer);
  };

  return (
    <div className="lesson">
      <div className="transcript" aria-live="polite">
        {turns.map((t) => (
          <article key={t.turn_id} className={`turn kind-${t.kind}${t.outcome ? ` outcome-${t.outcome}` : ""}${t.generated ? " generated" : ""}`}>
            <Markdown text={awaiting && t.turn_id === awaiting.turn_id && t.choices ? stripChoiceList(t.markdown) : t.markdown} />
            {t.generated && <p className="fine">Explained a different way (AI-assisted, checked by rules).</p>}
            {!t.awaiting && t.kind !== "status" && (t.kind === "explain" || t.kind === "correct") && (
              <div className="reactions">
                {REACTIONS.map(([k, label]) => (
                  <button key={k} className={`chip${reacted[t.turn_id] === k ? " on" : ""}`} onClick={() => react(t.turn_id, k)} data-track={`react.${k}`} disabled={!!reacted[t.turn_id]}>
                    {label}
                  </button>
                ))}
              </div>
            )}
          </article>
        ))}
        <div ref={bottom} />
      </div>

      {error && <p className="error" role="alert">{error === "stale_turn" ? "This question was already answered in another tab. Reloading…" : `Something went wrong (${error}). Your progress is saved; try again.`}</p>}

      {awaiting && !done && (
        <div className="answer-box">
          {awaiting.choices ? (
            <div className="choices">
              {awaiting.choices.map((c, i) => (
                <button key={i} className="btn choice" disabled={busy} onClick={() => submit(String(i + 1))} data-track="lesson.choice">
                  <span className="letter">{i + 1}.</span> {c}
                </button>
              ))}
            </div>
          ) : (
            <form onSubmit={onForm} className="free">
              <input aria-label="Your answer" value={answer} onChange={(e) => setAnswer(e.target.value)} maxLength={500} autoFocus disabled={busy} placeholder="Type your answer" />
              <button className="btn primary" disabled={busy || !answer.trim()} data-track="lesson.submit">Check</button>
            </form>
          )}
          {awaiting.expansions && awaiting.expansions.length > 0 && (
            <div className="hints">
              {awaiting.expansions.map((k) => (
                <button key={k} className="link" disabled={busy} onClick={() => hint(k)} data-track={`lesson.hint.${k}`}>
                  {awaiting.choices && k === "repeat_representation" ? "Review the lesson" : HINT_LABEL[k] || k.replace(/_/g, " ")}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="lesson-actions">
        {done ? (
          <button className="btn primary" onClick={() => navigate(`/summary/${sessionId}`)} data-track="lesson.summary">See summary</button>
        ) : (
          <button className="link" onClick={end} disabled={busy} data-track="lesson.end">Save and stop for now</button>
        )}
      </div>
    </div>
  );
}

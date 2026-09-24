import { useEffect, useState, type FormEvent } from "react";
import { api, ApiError, type PlayerView } from "../api";
import { Markdown } from "../markdown";
import { navigate } from "../router";
import FrameStepper from "../visuals/FrameStepper";
import Frame from "../visuals/Frame";
import VoiceControls from "../player/VoiceControls";
import TutorPanel from "../player/TutorPanel";
import FeedbackBar from "../player/FeedbackBar";
import { newIdempotencyKey } from "../api";

const STICKER = {
  correct: "/stickers/mascot-correct.svg",
  reassure: "/stickers/mascot-reassure.svg",
  done: "/stickers/mascot-done.svg",
};

export default function Player({ sessionId }: { sessionId: string }) {
  const [view, setView] = useState<PlayerView | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [answer, setAnswer] = useState("");
  const [answerModality, setAnswerModality] = useState<"text" | "voice">("text");
  const [showTeach, setShowTeach] = useState(false);
  const [tutorOpen, setTutorOpen] = useState(false);
  const [claimEmail, setClaimEmail] = useState("");
  const [claimPass, setClaimPass] = useState("");
  const [claimed, setClaimed] = useState(false);

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  const load = async () => {
    setBusy(true);
    try {
      const v = await api.playerGet(sessionId);
      setView(v);
      setAnswer("");
      setShowTeach(!v.step.teach_collapsed);
    } catch (e) {
      setError(e instanceof ApiError ? e.code : "error");
    } finally {
      setBusy(false);
    }
  };

  const attempt = async (response: string, kind: "text" | "voice" | "choice") => {
    if (!response.trim() || busy) return;
    setBusy(true);
    setError(null);
    try {
      const v = await api.playerAttempt(sessionId, response, kind, newIdempotencyKey());
      setView(v);
      setAnswer("");
    } catch (e) {
      setError(e instanceof ApiError ? e.code : "error");
    } finally {
      setBusy(false);
    }
  };

  const next = async () => {
    setBusy(true);
    setError(null);
    try {
      const v = await api.playerNext(sessionId);
      setView(v);
      setAnswer("");
      setShowTeach(!v.step.teach_collapsed);
    } catch (e) {
      setError(e instanceof ApiError ? e.code : "error");
    } finally {
      setBusy(false);
    }
  };

  const confused = async () => {
    setBusy(true);
    setError(null);
    try {
      const v = await api.playerConfused(sessionId);
      setView(v);
    } catch (e) {
      setError(e instanceof ApiError ? e.code : "error");
    } finally {
      setBusy(false);
    }
  };

  const claim = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      await api.claim(claimEmail, claimPass);
      setClaimed(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.code : "error");
    } finally {
      setBusy(false);
    }
  };

  if (error) return <p className="error" role="alert">Something went wrong ({error}).</p>;
  if (!view) return <p className="muted">Loading…</p>;

  const progressPct = view.progress.total > 0 ? (view.progress.done / view.progress.total) * 100 : 0;
  const speakText = `${view.step.teach_md} ${view.step.probe?.prompt_md || ""}`;

  return (
    <div className="player">
      <h1>{view.lesson.title}</h1>
      <div className="progress" aria-label={`Progress ${view.progress.done} of ${view.progress.total}`}>
        <div className="progress-bar" style={{ width: `${progressPct}%` }} />
        <span className="progress-label">{view.progress.done}/{view.progress.total}</span>
      </div>

      {view.phase !== "done" && (
        <>
          {view.step.teach_collapsed && !showTeach ? (
            <button className="btn small" onClick={() => setShowTeach(true)} data-track="player.show-teach">Show me again</button>
          ) : (
            <section className="teach card">
              <Markdown text={view.step.teach_md} />
              <FrameStepper frames={view.step.teach_frames} label="Teach frames" />
            </section>
          )}

          <section className="probe card">
            {view.step.probe && (
              <>
                <Markdown text={view.step.probe.prompt_md} />
                {view.step.probe.frames.map((frame, i) => (
                  <Frame key={i} frame={frame} />
                ))}
                <AnswerInput
                  probe={view.step.probe}
                  answer={answer}
                  setAnswer={(text) => { setAnswer(text); setAnswerModality("text"); }}
                  busy={busy}
                  onAnswer={(response, mod) => attempt(response, mod)}
                  modality={answerModality}
                />
                <VoiceControls
                  speakText={speakText}
                  onTranscript={(text) => {
                    setAnswer(text);
                    setAnswerModality("voice");
                  }}
                />
                <div className="probe-actions">
                  <button className="link" onClick={confused} disabled={busy} data-track="player.confused">I’m confused</button>
                  <button className="link" onClick={() => setTutorOpen(true)} disabled={busy} data-track="player.tutor">Ask the tutor</button>
                </div>
              </>
            )}
          </section>

          {view.phase === "feedback" && view.feedback && (
            <section className={`feedback card feedback-${view.feedback.outcome}`}>
              <Markdown text={view.feedback.message_md} />
              {view.feedback.frames.length > 0 && <FrameStepper frames={view.feedback.frames} label="Explain frames" />}
              {view.feedback.sticker && (
                <img
                  className="sticker"
                  src={STICKER[view.feedback.sticker]}
                  alt=""
                  width={120}
                  height={120}
                />
              )}
              <button
                className="btn primary"
                onClick={next}
                disabled={busy}
                data-track={view.feedback.next_action === "continue" ? "player.next" : "player.retry"}
              >
                {view.feedback.next_action === "continue" ? "Continue" : "Try again"}
              </button>
            </section>
          )}

          <FeedbackBar
            session_id={sessionId}
            step_id={view.step.step_id}
            target_kind="step"
            target_id={`${view.step.step_id}:${view.step.variant}`}
          />
        </>
      )}

      {view.phase === "done" && (
        <section className="done card">
          <img className="sticker" src={STICKER.done} alt="" width={120} height={120} />
          <h2>Lesson complete</h2>
          <p>You finished <strong>{view.lesson.title}</strong>.</p>
          {view.is_guest && !claimed ? (
            <div className="claim card">
              <h3>Save your progress</h3>
              <form onSubmit={claim}>
                <label>Email<input type="email" value={claimEmail} onChange={(e) => setClaimEmail(e.target.value)} required /></label>
                <label>Passphrase<input type="password" value={claimPass} onChange={(e) => setClaimPass(e.target.value)} required minLength={12} /></label>
                {error && <p className="error" role="alert">{error}</p>}
                <button className="btn primary" disabled={busy}>Save progress</button>
              </form>
            </div>
          ) : claimed ? (
            <p className="fine">Your progress is saved.</p>
          ) : null}
          <button className="btn primary" onClick={() => navigate("/")} data-track="player.home">Home</button>
        </section>
      )}

      <TutorPanel open={tutorOpen} onClose={() => setTutorOpen(false)} sessionId={sessionId} stepId={view.step.step_id} />
    </div>
  );
}

function AnswerInput({
  probe,
  answer,
  setAnswer,
  busy,
  onAnswer,
  modality,
}: {
  probe: NonNullable<PlayerView["step"]["probe"]>;
  answer: string;
  setAnswer: (s: string) => void;
  busy: boolean;
  onAnswer: (response: string, modality: "text" | "voice" | "choice") => void;
  modality: "text" | "voice";
}) {
  if (probe.answer_kind === "choice") {
    return (
      <div className="choices" role="group" aria-label="Choices">
        {probe.choices.map((c, i) => (
          <button key={i} className="btn choice" disabled={busy} onClick={() => onAnswer(c, "choice")} data-track={`player.choice.${i}`}>
            {c}
          </button>
        ))}
      </div>
    );
  }

  const type = probe.answer_kind === "integer" ? "number" : "text";
  const placeholder = probe.answer_kind === "fraction" ? "e.g. 3/4" : "Type your answer";
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onAnswer(answer, modality);
      }}
      className="free"
    >
      <input
        type={type}
        aria-label="Your answer"
        value={answer}
        onChange={(e) => setAnswer(e.target.value)}
        maxLength={500}
        disabled={busy}
        placeholder={placeholder}
      />
      <button className="btn primary" disabled={busy || !answer.trim()} data-track="player.check" type="submit">Check</button>
    </form>
  );
}

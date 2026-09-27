import { useEffect, useRef, useState, type FormEvent } from "react";
import { api, ApiError, type PlayerView } from "../api";
import { Markdown } from "../markdown";
import { navigate } from "../router";
import FrameStepper from "../visuals/FrameStepper";
import Frame from "../visuals/Frame";
import LessonMap, { getLessonSteps } from "../visuals/LessonMap";
import VoiceControls from "../player/VoiceControls";
import CompanionPanel from "../player/CompanionPanel";
import WorkedExampleCard from "../player/WorkedExampleCard";
import FeedbackBar from "../player/FeedbackBar";
import { applyPresentation } from "../player/presentation";
import Pet, { type PetMood } from "../mascot/Pet";
import RobotVisit from "../mascot/RobotVisit";
import { newIdempotencyKey } from "../api";
import ErrorBoundary from "../ErrorBoundary";

type RegenKind = "reexplain" | "example";

// Asking the tutor for another render of the *same* step/concept. The tutor
// answers with a versioned regenerate_presentation update, which is what the
// controls below adopt; a text-only reply leaves the view untouched.
const REGEN_PROMPTS: Record<RegenKind, string> = {
  reexplain: "Explain this step again with a different picture.",
  example: "Show a worked example for this step with a different picture.",
};

const REGEN_LABELS: Record<RegenKind, string> = {
  reexplain: "Explain again",
  example: "Worked example",
};

export default function Player({ sessionId }: { sessionId: string }) {
  const [view, setView] = useState<PlayerView | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [answer, setAnswer] = useState("");
  const [answerModality, setAnswerModality] = useState<"text" | "voice">("text");
  const [showTeach, setShowTeach] = useState(false);
  const [companionOpen, setCompanionOpen] = useState(false);
  const [petMood, setPetMood] = useState<PetMood>("wave");
  const [petHidden, setPetHidden] = useState(() => {
    if (typeof window === "undefined") return false;
    return localStorage.getItem("sos.pet.hidden") === "true";
  });
  const [companionSpeaking, setCompanionSpeaking] = useState(false);
  const [claimEmail, setClaimEmail] = useState("");
  const [claimPass, setClaimPass] = useState("");
  const [claimed, setClaimed] = useState(false);
  const moodTimerRef = useRef<number | null>(null);

  useEffect(() => {
    // A new session id (Resume, revisit, back/forward) must never render the
    // previous session's card, and must clear a sticky load error (#126).
    setView(null);
    setError(null);
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    localStorage.setItem("sos.pet.hidden", String(petHidden));
  }, [petHidden]);

  const setMood = (mood: PetMood, autoIdleMs?: number) => {
    setPetMood(mood);
    if (moodTimerRef.current) window.clearTimeout(moodTimerRef.current);
    if (autoIdleMs) {
      moodTimerRef.current = window.setTimeout(() => setPetMood("idle"), autoIdleMs);
    }
  };

  const load = async () => {
    setBusy(true);
    try {
      const v = await api.playerGet(sessionId);
      setView(v);
      setAnswer("");
      setShowTeach(!v.step.teach_collapsed);
      setMood("wave", 1200);
      setError(null);
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
      if (v.feedback?.outcome === "correct") setMood("celebrate", 1200);
      else setMood("encourage", 1200);
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
      setMood("encourage", 1200);
    } catch (e) {
      setError(e instanceof ApiError ? e.code : "error");
    } finally {
      setBusy(false);
    }
  };

  // Teach-panel regen chips must always do something useful.
  // Prefer deterministic adapt / confused paths so a silent tutor no-op cannot
  // leave Explain again / Worked example looking dead (#126 A12 / Ultrafast D004).
  const regenerate = async (kind: RegenKind) => {
    if (busy || !view) return;
    setBusy(true);
    setError(null);
    try {
      if (kind === "example") {
        // Keep teach open so the chip's effect is visible on the teaching surface.
        setShowTeach(true);
        const beforeMode = view.card_mode;
        const beforeMd = view.worked_example?.md || "";
        const v = await api.adapt(sessionId, "example");
        setView(v);
        setMood("encourage", 1200);
        // Backend rotates to an alternate example when already in worked_example
        // mode; if content somehow still matches, fall back to confused so the
        // fractions teach chip is never a silent no-op after resume.
        const afterMd = v.worked_example?.md || "";
        if (
          beforeMode === "worked_example" &&
          v.card_mode === "worked_example" &&
          afterMd === beforeMd
        ) {
          const fallback = await api.playerConfused(sessionId);
          setView(fallback);
        }
        return;
      }

      // Explain again: deterministic diagram/type swap first (adapt reexplain),
      // then tutor re-render, then confused — never prose-only / silent no-op.
      setShowTeach(true);
      let applied = false;
      try {
        const beforeFrames = JSON.stringify(view.step.teach_frames || []);
        const v = await api.adapt(sessionId, "reexplain");
        const afterFrames = JSON.stringify(v.step.teach_frames || []);
        if (afterFrames !== beforeFrames || v.variant_tag === "reexplain") {
          setView(v);
          setMood("encourage", 1200);
          applied = afterFrames !== beforeFrames;
          if (applied) return;
        } else {
          setView(v);
        }
      } catch {
        // Fall through.
      }
      try {
        const reply = await api.tutor(sessionId, REGEN_PROMPTS.reexplain);
        const next = applyPresentation(view, reply.regenerate_presentation);
        if (next !== view) {
          setView(next);
          applied = true;
        }
      } catch {
        // Fall through to confused.
      }
      if (!applied && view.phase === "probe" && view.step.probe) {
        const v = await api.playerConfused(sessionId);
        setView(v);
        setMood("encourage", 1200);
      }
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

  const retryLoad = () => {
    setView(null);
    setError(null);
    void load();
  };

  if (error) {
    return (
      <section className="card player-error" role="alert" data-testid="player-error">
        <h2>We couldn't load this lesson</h2>
        <p className="muted">Something went wrong ({error}). Your progress is saved.</p>
        <div className="render-error-actions">
          <button className="btn primary" onClick={retryLoad} disabled={busy} data-testid="player-error-retry">
            Retry
          </button>
          <button className="btn" onClick={() => navigate("/")} data-testid="player-error-home">
            Go home
          </button>
        </div>
      </section>
    );
  }
  if (!view || !view.step) return <p className="muted">Loading…</p>;
  const progressPct = view.progress.total > 0 ? (view.progress.done / view.progress.total) * 100 : 0;
  const speakText = `${view.step.teach_md} ${view.step.probe?.prompt_md || ""}`;
  const probeOpen = view.phase === "probe" && !!view.step.probe;

  return (
    <ErrorBoundary resetKey={sessionId} onRetry={retryLoad}>
    <div className="player">
      <div className="player-layout">
        <div className="player-main">
          <h1>{view.lesson.title}</h1>
          <LessonMap
            steps={getLessonSteps(view.lesson.lesson_id, view.lesson.total_steps)}
            currentIndex={view.step.index}
            completedIds={getLessonSteps(view.lesson.lesson_id, view.lesson.total_steps)
              .slice(0, view.step.index)
              .map((s) => s.id)}
            selectableCount={view.step.index}
            onSelect={view.can_revisit_step ? (i) => void revisit(i) : undefined}
          />
          <div className="progress" aria-label={`Progress ${view.progress.done} of ${view.progress.total}`}>
            <div className="progress-bar" style={{ width: `${progressPct}%` }} />
            <span className="progress-label">{view.progress.done}/{view.progress.total}</span>
          </div>

          {view.phase !== "done" && (
            <>
              {view.step.teach_collapsed && !showTeach ? (
                <button className="btn small" onClick={() => setShowTeach(true)} data-track="player.show-teach">
                  Show me again
                </button>
              ) : (
                <section className="teach card">
                  <Markdown text={view.step.teach_md} />
                  <FrameStepper frames={view.step.teach_frames} label="Teach frames" />
                  <div className="regen-controls" role="group" aria-label="Show this step another way">
                    {(Object.keys(REGEN_PROMPTS) as RegenKind[]).map((kind) => (
                      <button
                        key={kind}
                        type="button"
                        className="btn small"
                        onClick={() => void regenerate(kind)}
                        disabled={busy}
                        data-track={`player.regen.${kind}`}
                        data-testid={`player.step.regen-${kind}`}
                      >
                        {REGEN_LABELS[kind]}
                      </button>
                    ))}
                  </div>
                </section>
              )}

              {(view.step.probe || view.card_mode === "worked_example" || view.variant_tag) && (
              <section className="probe card">
                {(view.variant_tag || view.card_mode === "worked_example") && (
                  <div className="card-tags">
                    {view.card_mode === "worked_example" && <span className="tag worked-example-tag">Worked example</span>}
                    {view.variant_tag && <span className="tag variant-tag">{view.variant_tag}</span>}
                  </div>
                )}
                {view.card_mode === "worked_example" && <WorkedExampleCard example={view.worked_example} />}
                {view.step.probe && (
                  <>
                    <Markdown text={view.step.probe.prompt_md} />
                    {view.step.probe.frames.map((frame, i) => (
                      <Frame key={i} frame={frame} />
                    ))}

                    <AnswerInput
                      probe={view.step.probe}
                      answer={answer}
                      setAnswer={(text) => {
                        setAnswer(text);
                        setAnswerModality("text");
                      }}
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
                      <button className="link" onClick={confused} disabled={busy} data-track="player.confused">
                        I’m confused
                      </button>
                      <button className="link" onClick={() => setCompanionOpen(true)} disabled={busy} data-track="player.tutor">
                        Ask the tutor
                      </button>
                    </div>
                    {view.can_go_back && (
                      <div className="card-back">
                        <button className="btn small" onClick={() => void adaptBack()} disabled={busy} data-track="player.back">
                          Back
                        </button>
                      </div>
                    )}
                  </>
                )}
              </section>
              )}

              {/* Continue stays after teach / explain / worked — probe steps included (HESI fractions P0). */}
              {view.phase === "probe" && (view.card_mode === "worked_example" || !view.step.probe) && (
                <section className="probe card teach-advance" data-testid="player.teach-advance">
                  {view.card_mode === "worked_example" && view.can_go_back && (
                    <button
                      className="btn small"
                      onClick={() => void adaptBack()}
                      disabled={busy}
                      data-track="player.back"
                      data-testid="player.worked-example-back"
                    >
                      Back
                    </button>
                  )}
                  <button
                    className="btn primary"
                    onClick={next}
                    disabled={busy}
                    data-track="player.next"
                    data-testid="player.teach-continue"
                  >
                    Continue
                  </button>
                </section>
              )}

              {view.phase === "feedback" && view.feedback && (
                <section className={`feedback card feedback-${view.feedback.outcome}`}>
                  <Markdown text={view.feedback.message_md} />
                  {view.feedback.frames.length > 0 && <FrameStepper frames={view.feedback.frames} label="Explain frames" />}
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
                presentation_version={view.presentation_version}
              />
            </>
          )}

          {view.phase === "done" && (
            <section className="done card">
              <h2>Lesson complete</h2>
              <p>
                You finished <strong>{view.lesson.title}</strong>.
              </p>
              {view.is_guest && !claimed ? (
                <div className="claim card">
                  <h3>Save your progress</h3>
                  <form onSubmit={claim}>
                    <label>
                      Email
                      <input type="email" value={claimEmail} onChange={(e) => setClaimEmail(e.target.value)} required />
                    </label>
                    <label>
                      Passphrase
                      <input type="password" value={claimPass} onChange={(e) => setClaimPass(e.target.value)} required minLength={12} />
                    </label>
                    {error && <p className="error" role="alert">{error}</p>}
                    <button className="btn primary" disabled={busy}>
                      Save progress
                    </button>
                  </form>
                </div>
              ) : claimed ? (
                <p className="fine">Your progress is saved.</p>
              ) : null}
              <button className="btn primary" onClick={() => navigate("/")} data-track="player.home">
                Home
              </button>
            </section>
          )}
        </div>

        <div className="player-side">
          {companionOpen && (
            <CompanionPanel
              sessionId={sessionId}
              stepId={view.step.step_id}
              view={view}
              open={companionOpen}
              onClose={() => setCompanionOpen(false)}
              onViewChange={(v) => {
                setView(v);
              }}
              onSpeakingChange={(speaking) => {
                setCompanionSpeaking(speaking);
                if (speaking) setPetMood("talking");
              }}
              onBusyChange={(tutorBusy) => {
                if (tutorBusy) setPetMood("thinking");
                else setPetMood((m) => (m === "thinking" ? "idle" : m));
              }}
            />
          )}
          <RobotVisit
            petHidden={petHidden}
            probeOpen={probeOpen}
            typing={busy || !!answer}
            speaking={companionSpeaking}
            petTalking={petMood === "talking"}
            petThinking={petMood === "thinking"}
          />
        </div>
      </div>
      {/* Free-roam pet overlays the whole lesson viewport (not docked). */}
      <Pet
        mood={petMood}
        hidden={petHidden}
        onHiddenChange={setPetHidden}
        onTap={() => setCompanionOpen(true)}
        paused={probeOpen && !companionOpen && !companionSpeaking}
      />
    </div>
    </ErrorBoundary>
  );

  async function adaptBack() {
    setBusy(true);
    try {
      const v = await api.adapt(sessionId, "back");
      setView(v);
    } catch (e) {
      setError(e instanceof ApiError ? e.code : "error");
    } finally {
      setBusy(false);
    }
  }

  async function revisit(index: number) {
    setBusy(true);
    setError(null);
    try {
      const v = await api.adapt(sessionId, "step_back", index);
      setView(v);
      setAnswer("");
      setShowTeach(!v.step.teach_collapsed);
    } catch (e) {
      setError(e instanceof ApiError ? e.code : "error");
    } finally {
      setBusy(false);
    }
  }
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
      <button className="btn primary" disabled={busy || !answer.trim()} data-track="player.check" type="submit">
        Check
      </button>
    </form>
  );
}

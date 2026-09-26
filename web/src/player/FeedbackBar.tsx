import { useState, type FormEvent } from "react";
import { api, ApiError, type FeedbackReason } from "../api";

const REASONS: FeedbackReason[] = ["confusing", "too_long", "too_easy", "wrong", "not_helpful", "other"];

const REASON_LABEL: Record<string, string> = {
  confusing: "Confusing",
  too_long: "Too long",
  too_easy: "Too easy",
  wrong: "Wrong",
  not_helpful: "Not helpful",
  other: "Other",
};

export default function FeedbackBar({
  session_id,
  step_id,
  target_kind,
  target_id,
  presentation_version,
}: {
  session_id: string;
  step_id: string;
  target_kind: "step" | "tutor_message";
  target_id: string;
  presentation_version?: number;
}) {
  const [rating, setRating] = useState<"like" | "dislike" | null>(null);
  const [reasons, setReasons] = useState<FeedbackReason[]>([]);
  const [freeText, setFreeText] = useState("");
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);

  // The learner step review is a deliberate Submit, not an instant reaction.
  if (target_kind === "step") {
    return (
      <StepReviewForm
        session_id={session_id}
        step_id={step_id}
        target_id={target_id}
        presentation_version={presentation_version ?? 0}
      />
    );
  }

  const send = async (r: "like" | "dislike", reasonsToSend: FeedbackReason[] = [], text?: string) => {
    setBusy(true);
    try {
      await api.feedback({ session_id, step_id, target_kind, target_id, rating: r, reasons: reasonsToSend, free_text: text });
      setSent(true);
    } finally {
      setBusy(false);
    }
  };

  if (sent) {
    return <p className="feedback-thanks">Thanks — this helps us improve.</p>;
  }

  if (rating === "dislike") {
    return (
      <div className="feedback-form" role="form" aria-label="Feedback reasons">
        <div className="feedback-chips">
          {REASONS.map((reason) => (
            <button
              key={reason}
              type="button"
              className={`chip${reasons.includes(reason) ? " on" : ""}`}
              onClick={() =>
                setReasons((prev) => (prev.includes(reason) ? prev.filter((x) => x !== reason) : [...prev, reason]))
              }
              disabled={busy}
              data-track={`feedback.reason.${reason}`}
            >
              {REASON_LABEL[reason]}
            </button>
          ))}
        </div>
        {reasons.includes("other") && (
          <textarea
            aria-label="Other feedback"
            maxLength={500}
            value={freeText}
            onChange={(e) => setFreeText(e.target.value)}
            placeholder="Tell us more (optional)"
            rows={2}
          />
        )}
        <button
          className="btn small"
          disabled={busy || reasons.length === 0}
          onClick={() => send("dislike", reasons, freeText || undefined)}
          data-track="feedback.send"
        >
          Send
        </button>
      </div>
    );
  }

  return (
    <div className="feedback-bar" role="group" aria-label="Was this helpful?">
      <button
        className={`chip${rating === "like" ? " on" : ""}`}
        onClick={() => {
          setRating("like");
          void send("like");
        }}
        disabled={busy}
        aria-label="Helpful"
        data-track="feedback.like"
      >
        👍
      </button>
      <button
        className="chip"
        onClick={() => setRating("dislike")}
        disabled={busy}
        aria-label="Not helpful"
        data-track="feedback.dislike"
      >
        👎
      </button>
    </div>
  );
}

const RATING_LABEL: Record<number, string> = {
  1: "Not useful",
  2: "Slightly useful",
  3: "Useful",
  4: "Very useful",
  5: "Extremely useful",
};

type StepReviewDraft = {
  rating: number | null;
  why: string;
  key: string;
  sent: boolean;
};

function reviewKey(): string {
  if (typeof crypto.randomUUID === "function") return crypto.randomUUID();
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

function newStepReviewDraft(): StepReviewDraft {
  return { rating: null, why: "", key: reviewKey(), sent: false };
}

// One optional review of the current step: choose 1-5, type why, press Submit.
// Choosing or typing never calls the API; a same-step re-render keeps the draft
// and its idempotency key, and a changed step/variant starts a new review.
function StepReviewForm({
  session_id,
  step_id,
  target_id,
  presentation_version,
}: {
  session_id: string;
  step_id: string;
  target_id: string;
  presentation_version: number;
}) {
  const identity = `${session_id}:${step_id}:${target_id}`;
  const [draft, setDraft] = useState<StepReviewDraft>(newStepReviewDraft);
  const [draftIdentity, setDraftIdentity] = useState(identity);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (draftIdentity !== identity) {
    setDraftIdentity(identity);
    setDraft(newStepReviewDraft());
    setError(null);
  }

  const why = draft.why.trim();
  const ready = draft.rating !== null && why.length > 0;

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (draft.rating === null || !why || busy) return;
    setBusy(true);
    setError(null);
    try {
      await api.feedback({
        session_id,
        step_id,
        target_kind: "step",
        target_id,
        presentation_version,
        rating: draft.rating,
        free_text: why,
        idempotency_key: draft.key,
      });
      setDraft((prev) => ({ ...prev, sent: true }));
    } catch (e) {
      // Keep the draft and its key: a retry is the same review intent.
      setError(e instanceof ApiError ? e.code : "error");
    } finally {
      setBusy(false);
    }
  };

  if (draft.sent) {
    return (
      <div className="feedback-form step-review" role="group" aria-label="Step review saved">
        <p className="feedback-thanks">Thanks, your review of this step was saved.</p>
        <button
          type="button"
          className="btn small"
          onClick={() => setDraft(newStepReviewDraft())}
          data-track="feedback.review_again"
        >
          Review again
        </button>
      </div>
    );
  }

  return (
    <form className="feedback-form step-review" aria-label="Rate this step" onSubmit={submit}>
      <fieldset className="feedback-scale">
        <legend>How useful was this step?</legend>
        <div className="feedback-chips" role="group" aria-label="Rate this step from 1 to 5">
          {[1, 2, 3, 4, 5].map((score) => (
            <button
              key={score}
              type="button"
              className={`chip${draft.rating === score ? " on" : ""}`}
              aria-label={`Rate ${score} out of 5`}
              aria-pressed={draft.rating === score}
              onClick={() => setDraft((prev) => ({ ...prev, rating: score }))}
              disabled={busy}
              data-track={`feedback.rate.${score}`}
            >
              {score}
            </button>
          ))}
        </div>
        <p className="fine">
          {draft.rating === null
            ? "1 is not useful, 5 is extremely useful."
            : `${draft.rating} out of 5: ${RATING_LABEL[draft.rating]}`}
        </p>
      </fieldset>
      <label className="feedback-why">
        Why this rating?
        <textarea
          aria-label="Why this rating?"
          maxLength={500}
          rows={2}
          value={draft.why}
          onChange={(e) => setDraft((prev) => ({ ...prev, why: e.target.value }))}
          placeholder="What was right, wrong, or unclear about this step?"
        />
      </label>
      {error && <p className="error">Could not save your review ({error}).</p>}
      <button type="submit" className="btn primary" disabled={!ready || busy} data-track="feedback.submit">
        {busy ? "Submitting" : "Submit"}
      </button>
    </form>
  );
}

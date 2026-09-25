import { useState } from "react";
import { api, type FeedbackBody } from "../api";

const REASONS: FeedbackBody["reasons"] = ["confusing", "too_long", "too_easy", "wrong", "not_helpful", "other"];

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
}: {
  session_id: string;
  step_id: string;
  target_kind: "step" | "tutor_message";
  target_id: string;
}) {
  const [rating, setRating] = useState<"like" | "dislike" | null>(null);
  const [reasons, setReasons] = useState<FeedbackBody["reasons"]>([]);
  const [freeText, setFreeText] = useState("");
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);

  const send = async (r: "like" | "dislike", reasonsToSend: FeedbackBody["reasons"] = [], text?: string) => {
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

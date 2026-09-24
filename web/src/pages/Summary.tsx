import { useEffect, useState } from "react";
import { api } from "../api";
import { navigate } from "../router";

type S = Awaited<ReturnType<typeof api.summary>>;

export default function Summary({ sessionId }: { sessionId: string }) {
  const [s, setS] = useState<S | null>(null);
  useEffect(() => {
    api.summary(sessionId).then(setS).catch(() => setS(null));
  }, [sessionId]);
  if (!s) return <p className="muted">Loading…</p>;
  const next = s.next_review_at ? new Date(s.next_review_at).toLocaleString() : null;
  return (
    <section className="card narrow">
      <h1>Session summary</h1>
      <p className="big">{s.correct} of {s.attempts} answers correct</p>
      {next && <p>Next review: {next}</p>}
      <p className="fine">{s.note}</p>
      <button className="btn primary" onClick={() => navigate("/")} data-track="summary.home">Back to home</button>
    </section>
  );
}

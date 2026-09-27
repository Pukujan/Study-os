import { useEffect, useState } from "react";
import { api, ApiError, type AdminFeedback as AdminFeedbackData, type Me } from "../api";

export default function AdminFeedback({ me }: { me: Me }) {
  const [data, setData] = useState<AdminFeedbackData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .adminFeedback()
      .then(setData)
      .catch((e) => setError(e instanceof ApiError ? e.code : "error"));
  }, []);

  if (me.role !== "admin") {
    return <p className="error">Admins only</p>;
  }

  if (error) return <p className="error">Could not load feedback ({error}).</p>;
  if (!data) return <p className="muted">Loading…</p>;

  return (
    <section className="admin-feedback">
      <h1>Feedback</h1>
      <h2>Tutor thumbs by prompt version</h2>
      <table className="feedback-table">
        <thead>
          <tr><th>Prompt version</th><th>Likes</th><th>Dislikes</th><th>Top reasons</th></tr>
        </thead>
        <tbody>
          {data.by_prompt_version.map((row) => (
            <tr key={row.prompt_version}>
              <td>{row.prompt_version}</td>
              <td>{row.likes}</td>
              <td>{row.dislikes}</td>
              <td>{row.top_reasons.map((r) => `${r.reason} (${r.count})`).join(", ") || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Step reviews (1-5, self-report)</h2>
      <p className="muted">
        Ordinal learner opinion of one presentation version. Not a mastery or correctness score, and not
        comparable with the historical thumbs above.
      </p>
      <table className="feedback-table">
        <thead>
          <tr><th>Presentation version</th><th>1</th><th>2</th><th>3</th><th>4</th><th>5</th><th>Total</th></tr>
        </thead>
        <tbody>
          {data.step_reviews.map((row) => (
            <tr key={row.presentation_version ?? "unversioned"}>
              <td>{row.presentation_version ?? "—"}</td>
              {[1, 2, 3, 4, 5].map((score) => (
                <td key={score}>{row.counts[String(score)] ?? 0}</td>
              ))}
              <td>{row.total}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Latest feedback</h2>
      <table className="feedback-table">
        <thead>
          <tr><th>Time</th><th>Rating</th><th>Reasons</th><th>Target</th><th>Step</th><th>Version</th><th>Prompt / Model</th><th>Free text</th></tr>
        </thead>
        <tbody>
          {data.rows.map((row, i) => (
            <tr key={i}>
              <td>{row.created_at}</td>
              <td>{row.rating}</td>
              <td>{row.reasons.join(", ") || "—"}</td>
              <td>{row.target_kind}</td>
              <td>{row.step_id || row.target_id}</td>
              <td>{row.presentation_version ?? "—"}</td>
              <td>{row.prompt_version || "—"} / {row.model || "—"}</td>
              <td>{row.free_text_scrubbed || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

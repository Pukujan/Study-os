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
      <h2>By prompt version</h2>
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

      <h2>Latest feedback</h2>
      <table className="feedback-table">
        <thead>
          <tr><th>Time</th><th>Rating</th><th>Reasons</th><th>Target</th><th>Step</th><th>Prompt / Model</th><th>Free text</th></tr>
        </thead>
        <tbody>
          {data.rows.map((row, i) => (
            <tr key={i}>
              <td>{row.time}</td>
              <td>{row.rating}</td>
              <td>{row.reasons.join(", ") || "—"}</td>
              <td>{row.target_kind}</td>
              <td>{row.step}</td>
              <td>{row.prompt_version || "—"} / {row.model || "—"}</td>
              <td>{row.free_text || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

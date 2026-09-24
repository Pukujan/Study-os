import { useState } from "react";
import { api, ApiError, type Me } from "../api";
import { navigate } from "../router";

const LESSONS = [
  { lesson_id: "fractions-compare", title: "Comparing fractions", lane: "HESI A2 prep" },
  { lesson_id: "sliding-window-box", title: "Sliding window: the box", lane: "Algorithms (DSA)" },
];

export default function Try({ onSignedIn }: { onSignedIn: (me: Me) => void }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const tryLesson = async (lessonId: string) => {
    setBusy(true);
    setError(null);
    try {
      const { me, session } = await api.tryLesson(lessonId);
      onSignedIn(me);
      navigate(`/play/${session.session_id}`);
    } catch (e) {
      setError(e instanceof ApiError ? e.code : "error");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="card try-page">
      <h1>Learn one small idea at a time</h1>
      <p className="muted">Short, visual lessons that build one concept at a time.</p>
      {error && <p className="error" role="alert">Could not start lesson ({error}).</p>}
      <ul className="lessons">
        {LESSONS.map((lesson) => (
          <li key={lesson.lesson_id} className="lesson-item">
            <div>
              <div className="lesson-title">{lesson.title}</div>
              <div className="lane-label muted">{lesson.lane}</div>
            </div>
            <button
              className="btn primary"
              disabled={busy}
              onClick={() => tryLesson(lesson.lesson_id)}
              data-track="try.start"
            >
              Try it — no account needed
            </button>
          </li>
        ))}
      </ul>
      <button className="link" onClick={() => navigate("/login")} data-track="try.signin">
        Already have an account? Sign in
      </button>
    </section>
  );
}

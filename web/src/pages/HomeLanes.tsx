import { useEffect, useState } from "react";
import { api, ApiError, type LanesPayload, type Me } from "../api";
import { navigate } from "../router";

const STATE_LABEL: Record<string, string> = {
  not_started: "Start",
  in_progress: "Resume",
  done: "Review",
};

const LANE_ART: Record<string, string> = {
  dsa: "/art/lane-dsa.webp",
  hesi: "/art/lane-hesi.webp",
  ai: "/art/lane-ai.webp",
  "study-os": "/art/lane-studyos.webp",
};

const LANE_ART_ALT: Record<string, string> = {
  dsa: "A focused learner works through algorithms with a robot helper nearby.",
  hesi: "A calm study scene for HESI prep with the learner reviewing notes.",
  ai: "The learner explores AI concepts with sketches and diagrams around them.",
  "study-os": "The learner stands in a bright Study OS workspace ready to learn.",
};

export default function HomeLanes({ me }: { me?: Me }) {
  const [data, setData] = useState<LanesPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api
      .lanes()
      .then(setData)
      .catch((e) => setError(e instanceof ApiError ? e.code : "error"));
  }, []);

  const startLesson = async (lessonId: string) => {
    setBusy(true);
    try {
      const view = await api.playerStart(lessonId);
      navigate(`/play/${view.session_id}`);
    } catch (e) {
      setError(e instanceof ApiError ? e.code : "error");
      setBusy(false);
    }
  };

  const continueAction = async () => {
    if (!data) return;
    setBusy(true);
    try {
      if (data.continue.session_id) {
        navigate(`/play/${data.continue.session_id}`);
      } else {
        const view = await api.playerStart(data.continue.lesson_id);
        navigate(`/play/${view.session_id}`);
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.code : "error");
    } finally {
      setBusy(false);
    }
  };

  const startLegacyDsa = async () => {
    setBusy(true);
    try {
      const view = await api.start({ track: "dsa" });
      navigate(`/lesson/${view.session_id}`);
    } catch (e) {
      setError(e instanceof ApiError ? e.code : "error");
    } finally {
      setBusy(false);
    }
  };

  if (error) return <p className="error">Could not load lanes ({error}).</p>;
  if (!data) return <p className="muted">Loading…</p>;

  const greeting = me?.display_name ? `Hi, ${me.display_name}!` : me?.handle ? `Hi, ${me.handle}!` : "Hi!";

  return (
    <div className="home-lanes">
      <section className="hello">
        <h1>{greeting}</h1>
        <p className="muted">Pick up where you left off or explore a lane.</p>
      </section>

      <section className="continue-section">
        <button className="btn primary continue-btn" onClick={continueAction} disabled={busy} data-track="home.continue">
          {data.continue.label}
        </button>
      </section>

      <section className="lanes-grid">
        {data.lanes.map((lane) => (
          <article key={lane.lane_id} className="card lane-card">
            <div className="lane-art-wrapper">
              <img
                className="lane-art"
                src={LANE_ART[lane.lane_id]}
                alt={LANE_ART_ALT[lane.lane_id]}
                loading="lazy"
              />
            </div>
            <h2>{lane.title}</h2>
            <p className="muted">{lane.blurb}</p>
            {lane.status === "in_progress_content" ? (
              <p className="muted">First lesson in progress</p>
            ) : (
              <ul className="lessons">
                {lane.lessons.map((lesson) => (
                  <li key={lesson.lesson_id} className="lesson-item">
                    <span className="lesson-title">{lesson.title}</span>
                    <span className="lesson-progress muted">
                      {lesson.progress.done}/{lesson.progress.total}
                    </span>
                    <button
                      className="btn small"
                      disabled={busy}
                      onClick={() => startLesson(lesson.lesson_id)}
                      data-track="home.lesson.start"
                    >
                      {STATE_LABEL[lesson.state] || "Start"}
                    </button>
                  </li>
                ))}
              </ul>
            )}
            {lane.legacy?.kind === "dsa_pir" && (
              <button className="btn small" onClick={startLegacyDsa} disabled={busy} data-track="home.dsa.classic">
                {lane.legacy.label}
              </button>
            )}
          </article>
        ))}
      </section>
    </div>
  );
}

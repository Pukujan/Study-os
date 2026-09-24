import { useEffect, useState } from "react";
import { api, ApiError, type Home as HomeData, type Section } from "../api";
import { navigate } from "../router";

const STATE_LABEL: Record<string, string> = {
  not_started: "Not started",
  in_progress: "In progress",
  assembled: "Done today — review later",
  checkpoint_passed: "Checkpoint passed",
};

export default function Home() {
  const [data, setData] = useState<HomeData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.home().then(setData).catch((e) => setError(e instanceof ApiError ? e.code : "error"));
  }, []);

  const start = async (body: { track: string; topic_id?: string; checkpoint?: string }) => {
    setBusy(true);
    try {
      const view = await api.start(body);
      navigate(`/lesson/${view.session_id}`);
    } catch (e) {
      setError(e instanceof ApiError ? e.code : "error");
      setBusy(false);
    }
  };

  if (error) return <p className="error">Could not load your home page ({error}).</p>;
  if (!data) return <p className="muted">Loading…</p>;

  const a2 = data.hesi.sections.filter((s) => s.exam_id === "a2");
  const exit = data.hesi.sections.filter((s) => s.exam_id !== "a2");
  const rec = data.hesi.recommended_topic;
  const recTitle = a2.flatMap((s) => s.topics).find((t) => t.topic_id === rec)?.title;

  return (
    <div className="home">
      <section className="hello">
        <h1>Hi {data.display_name || data.handle}</h1>
        <p className="muted">
          {data.streak_days > 0 ? `${data.streak_days}-day streak. ` : ""}
          {data.hesi.reviews_due > 0 ? `${data.hesi.reviews_due} review item(s) due; they’ll warm you up at the start of your next topic.` : ""}
        </p>
      </section>

      <section className="card">
        <h2>HESI A2 prep</h2>
        <p className="banner" role="note">
          <strong>Draft content.</strong> These practice questions were written with AI help and have not been reviewed yet. If something looks wrong, tap “I’m confused” on it.
        </p>
        {rec && (
          <button className="btn primary" disabled={busy} onClick={() => start({ track: "hesi", topic_id: rec })} data-track="home.recommended">
            Continue: {recTitle}
          </button>
        )}
        {a2.map((s) => (
          <SectionView key={s.section_id} section={s} busy={busy} onTopic={(t) => start({ track: "hesi", topic_id: t })} onCheckpoint={() => start({ track: "hesi", checkpoint: s.section_id })} />
        ))}
        {exit.length > 0 && (
          <details className="exit">
            <summary>HESI Exit (coming later)</summary>
            {exit.map((s) => (
              <p key={s.section_id} className="muted">{s.title}: {s.topics.length} topic(s) planned.</p>
            ))}
          </details>
        )}
      </section>

      <section className="card">
        <h2>Algorithms: sliding window</h2>
        <p className="muted">
          {data.dsa.current_step ? `You’re partway through (step ${data.dsa.current_step}).` : data.dsa.status ? `Last status: ${data.dsa.status.replace(/_/g, " ")}.` : "A step-by-step lesson on the sliding-window sum."}
        </p>
        <button className="btn" disabled={busy} onClick={() => start({ track: "dsa" })} data-track="home.dsa">
          {data.dsa.current_step ? "Resume lesson" : "Start lesson"}
        </button>
      </section>
    </div>
  );
}

function SectionView({ section, busy, onTopic, onCheckpoint }: { section: Section; busy: boolean; onTopic: (id: string) => void; onCheckpoint: () => void }) {
  const done = section.topics.filter((t) => t.state === "assembled" || t.state === "checkpoint_passed").length;
  return (
    <div className="section">
      <h3>
        {section.title} <span className="muted small">{done}/{section.topics.length}</span>
      </h3>
      <ul className="topics">
        {section.topics.map((t) => (
          <li key={t.topic_id} className={`topic state-${t.state}`}>
            <button className="topic-btn" disabled={busy || !t.available} onClick={() => onTopic(t.topic_id)} data-track="home.topic" title={t.prerequisites_met ? "" : "Earlier topics first is recommended"}>
              <span className="dot" aria-hidden="true" />
              <span className="t-title">{t.title}</span>
              <span className="t-state">{t.available ? STATE_LABEL[t.state] || t.state : "Not ready yet"}</span>
            </button>
          </li>
        ))}
      </ul>
      <button className="btn small" disabled={busy || done === 0} onClick={onCheckpoint} data-track="home.checkpoint">
        {section.checkpoint_state === "checkpoint_passed" ? "Retake checkpoint" : "Section checkpoint"}
      </button>
    </div>
  );
}

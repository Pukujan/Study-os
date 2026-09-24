import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import { Markdown } from "../markdown";
import FeedbackBar from "./FeedbackBar";

export default function TutorPanel({
  open,
  onClose,
  sessionId,
  stepId,
}: {
  open: boolean;
  onClose: () => void;
  sessionId: string;
  stepId: string;
}) {
  const [messages, setMessages] = useState<TutorMessage[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const media = window.matchMedia("(max-width: 1023px)");
    setIsMobile(media.matches);
    const onResize = () => setIsMobile(media.matches);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  useEffect(() => {
    if (!open || !isMobile || !panelRef.current) return;
    const panel = panelRef.current;
    const focusables = Array.from(panel.querySelectorAll<HTMLElement>("button, [href], input, textarea, select, [tabindex]:not([tabindex='-1'])"));
    const first = focusables[0];
    if (first) first.focus();

    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
        return;
      }
      if (e.key !== "Tab") return;
      const list = Array.from(panel.querySelectorAll<HTMLElement>("button, [href], input, textarea, select, [tabindex]:not([tabindex='-1'])"));
      if (list.length === 0) return;
      const firstEl = list[0];
      const lastEl = list[list.length - 1];
      if (e.shiftKey) {
        if (document.activeElement === firstEl) {
          e.preventDefault();
          lastEl.focus();
        }
      } else {
        if (document.activeElement === lastEl) {
          e.preventDefault();
          firstEl.focus();
        }
      }
    };
    panel.addEventListener("keydown", onKey);
    return () => panel.removeEventListener("keydown", onKey);
  }, [open, isMobile, onClose]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, open]);

  const send = async (e?: React.FormEvent) => {
    e?.preventDefault();
    const text = input.trim();
    if (!text || busy) return;
    setBusy(true);
    setMessages((m) => [...m, { role: "learner", text }]);
    setInput("");
    try {
      const reply = await api.tutor(sessionId, text);
      setMessages((m) => [...m, { role: "tutor", text: reply.reply_md, id: reply.message_id }]);
    } catch {
      setMessages((m) => [...m, { role: "tutor", text: "Sorry, I couldn’t reach the tutor. Try again in a moment.", id: "" }]);
    } finally {
      setBusy(false);
    }
  };

  if (!open) return null;

  return (
    <div className={`tutor-panel-backdrop${isMobile ? " mobile" : ""}`} onClick={onClose}>
      <div
        ref={panelRef}
        className={`tutor-panel${isMobile ? " mobile" : ""}`}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-label="Tutor chat"
      >
        <div className="tutor-header">
          <h3>Tutor</h3>
          <button className="link" onClick={onClose} data-track="tutor.close">Close</button>
        </div>
        <div className="tutor-messages">
          {messages.length === 0 && (
            <p className="fine">The tutor won’t give you the answer, but it will help you get there.</p>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`tutor-message ${m.role}`}>
              {m.role === "tutor" ? (
                <>
                  <div className="tutor-bubble"><Markdown text={m.text} /></div>
                  {m.id && (
                    <FeedbackBar
                      session_id={sessionId}
                      step_id={stepId}
                      target_kind="tutor_message"
                      target_id={m.id}
                    />
                  )}
                </>
              ) : (
                <div className="tutor-bubble learner">{m.text}</div>
              )}
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
        <form onSubmit={send} className="tutor-input">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            maxLength={500}
            placeholder="Ask the tutor..."
            disabled={busy}
            aria-label="Message"
          />
          <button className="btn primary" disabled={busy || !input.trim()} data-track="tutor.send">Send</button>
        </form>
      </div>
    </div>
  );
}

type TutorMessage = { role: "learner"; text: string } | { role: "tutor"; text: string; id?: string };

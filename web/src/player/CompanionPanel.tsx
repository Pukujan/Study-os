import { useEffect, useRef, useState } from "react";
import { api, type PlayerView, type TutorReply } from "../api";
import { Markdown } from "../markdown";
import FeedbackBar from "./FeedbackBar";
import { applyPresentation } from "./presentation";
import Sprite from "../mascot/Sprite";

type ChatItem =
  | { id: string; role: "learner"; text: string }
  | {
      id: string;
      role: "tutor";
      text: string;
      served: string;
      prompt_version: string;
      model: string;
      suggested_action?: string | null;
      regenerate_presentation?: TutorReply["regenerate_presentation"];
    }
  | { id: string; role: "system"; text: string };

const STORAGE_KEY = (sessionId: string) => `sos.chat.${sessionId}`;

const srCtor =
  typeof window !== "undefined"
    ? (window as unknown as { SpeechRecognition?: unknown; webkitSpeechRecognition?: unknown }).SpeechRecognition ||
      (window as unknown as { SpeechRecognition?: unknown; webkitSpeechRecognition?: unknown }).webkitSpeechRecognition
    : undefined;

function loadHistory(sessionId: string): ChatItem[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY(sessionId));
    if (!raw) return [];
    return JSON.parse(raw) as ChatItem[];
  } catch {
    return [];
  }
}

function saveHistory(sessionId: string, history: ChatItem[]) {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.setItem(STORAGE_KEY(sessionId), JSON.stringify(history));
  } catch {
    /* ignore */
  }
}

export type CompanionPanelProps = {
  sessionId: string;
  stepId: string;
  view: PlayerView;
  open: boolean;
  onClose: () => void;
  onViewChange: (view: PlayerView) => void;
  onSpeakingChange?: (speaking: boolean) => void;
  onBusyChange?: (busy: boolean) => void;
};

export default function CompanionPanel({
  sessionId,
  stepId,
  view,
  open,
  onClose,
  onViewChange,
  onSpeakingChange,
  onBusyChange,
}: CompanionPanelProps) {
  const [history, setHistory] = useState<ChatItem[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [speakerOn, setSpeakerOn] = useState(() => {
    if (typeof window === "undefined") return false;
    return localStorage.getItem("sos.companion.speaker") === "true";
  });
  const [micOn, setMicOn] = useState(false);
  const [spokenTo, setSpokenTo] = useState(0);
  const [speaking, setSpeaking] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<{ stop: () => void } | null>(null);
  const latestTutorRef = useRef<string | null>(null);

  useEffect(() => {
    setHistory(loadHistory(sessionId));
  }, [sessionId]);

  useEffect(() => {
    saveHistory(sessionId, history);
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history, sessionId]);

  useEffect(() => {
    onBusyChange?.(busy);
  }, [busy, onBusyChange]);

  useEffect(() => {
    if (!open) return;
    const panel = document.querySelector(".companion-panel");
    if (!panel) return;
    const focusables = Array.from(panel.querySelectorAll<HTMLElement>("button, [href], input, textarea, select, [tabindex]:not([tabindex='-1'])"));
    const first = focusables[0];
    if (first) first.focus();

    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
        return;
      }
      if (e.key !== "Tab") return;
      if (focusables.length === 0) return;
      const firstEl = focusables[0];
      const lastEl = focusables[focusables.length - 1];
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
    panel.addEventListener("keydown", onKey as EventListener);
    return () => panel.removeEventListener("keydown", onKey as EventListener);
  }, [open, onClose]);

  useEffect(() => {
    if (!speaking) setSpokenTo(0);
  }, [speaking]);

  const speakLatest = (text: string) => {
    if (typeof window === "undefined" || !window.speechSynthesis) return;
    latestTutorRef.current = text;
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(text);
    utter.onboundary = (e) => setSpokenTo(e.charIndex + e.charLength);
    utter.onstart = () => {
      setSpeaking(true);
      onSpeakingChange?.(true);
    };
    utter.onend = () => {
      setSpeaking(false);
      onSpeakingChange?.(false);
      setSpokenTo(text.length);
    };
    utter.onerror = () => {
      setSpeaking(false);
      onSpeakingChange?.(false);
    };
    window.speechSynthesis.speak(utter);
  };

  const stopSpeaking = () => {
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    setSpeaking(false);
    onSpeakingChange?.(false);
  };

  const pushSystem = (text: string) => {
    setHistory((h) => [...h, { id: cryptoRandomId(), role: "system", text }]);
  };

  const tutorReplyToItem = (reply: TutorReply): ChatItem => ({
    id: reply.message_id || cryptoRandomId(),
    role: "tutor",
    text: reply.reply_md,
    served: reply.served,
    prompt_version: reply.prompt_version,
    model: reply.model,
    suggested_action: (reply as { suggested_action?: string | null }).suggested_action,
    regenerate_presentation: reply.regenerate_presentation,
  });

  const send = async () => {
    const text = input.trim();
    if (!text || busy) return;
    setHistory((h) => [...h, { id: cryptoRandomId(), role: "learner", text }]);
    setInput("");
    setBusy(true);
    try {
      const reply = await api.tutor(sessionId, text);
      const item = tutorReplyToItem(reply);
      setHistory((h) => [...h, item]);
      const nextView = applyPresentation(view, reply.regenerate_presentation);
      if (nextView !== view) onViewChange(nextView);
      if (speakerOn) speakLatest(item.text);
    } catch {
      setHistory((h) => [
        ...h,
        { id: cryptoRandomId(), role: "tutor", text: "Sorry, I couldn’t reach the tutor. Try again in a moment.", served: "fallback", prompt_version: "", model: "" },
      ]);
    } finally {
      setBusy(false);
    }
  };

  const handleChip = async (kind: "example" | "easier" | "harder" | "reexplain") => {
    if (view.phase === "probe") return;
    setBusy(true);
    try {
      if (kind === "reexplain") {
        pushSystem("Explained again.");
        const v = await api.playerConfused(sessionId);
        onViewChange(v);
      } else {
        pushSystem(`Updated the card: ${chipLabel(kind).toLowerCase()}.`);
        const v = await api.adapt(sessionId, kind);
        onViewChange(v);
      }
    } catch {
      // ignore
    } finally {
      setBusy(false);
    }
  };

  const back = async () => {
    setBusy(true);
    try {
      const v = await api.adapt(sessionId, "back");
      onViewChange(v);
    } finally {
      setBusy(false);
    }
  };

  const toggleMic = () => {
    if (micOn) {
      recognitionRef.current?.stop();
      setMicOn(false);
      return;
    }
    if (!srCtor || typeof srCtor !== "function") return;
    type SRResult = { 0: { transcript: string }; isFinal?: boolean };
    const Recognition = srCtor as unknown as new () => {
      lang: string;
      interimResults: boolean;
      onresult: ((ev: { results: ArrayLike<SRResult> }) => void) | null;
      onend: (() => void) | null;
      onerror: (() => void) | null;
      start: () => void;
      stop: () => void;
    };
    const rec = new Recognition();
    rec.lang = "en-US";
    rec.interimResults = true;
    let active = true;
    rec.onresult = (event) => {
      let finalText = "";
      let interim = "";
      for (let i = 0; i < event.results.length; i++) {
        const result = event.results[i];
        const transcript = result[0].transcript;
        if (result.isFinal) finalText += transcript;
        else interim += transcript;
      }
      setInput((finalText + interim).trimStart());
    };
    rec.onend = () => {
      if (active) setMicOn(false);
    };
    rec.onerror = () => {
      active = false;
      setMicOn(false);
    };
    recognitionRef.current = { stop: () => { active = false; rec.stop(); } };
    rec.start();
    setMicOn(true);
  };

  const toggleSpeaker = () => {
    const next = !speakerOn;
    setSpeakerOn(next);
    if (typeof window !== "undefined") localStorage.setItem("sos.companion.speaker", String(next));
    if (!next) {
      stopSpeaking();
    } else {
      const latest = latestTutorRef.current;
      if (latest) speakLatest(latest);
    }
  };

  const latestSuggested = history.length > 0 && history[history.length - 1].role === "tutor" ? history[history.length - 1] : null;
  const suggestedAction = latestSuggested && "suggested_action" in latestSuggested ? latestSuggested.suggested_action : undefined;
  const isProbe = view.phase === "probe";

  if (!open) return null;

  return (
    <div className="companion-panel" role="dialog" aria-label="Study buddy">
      <div className="companion-panel-inner">
        <div className="companion-header">
          <div className="companion-header-left">
            <div className="companion-avatar">
              <Sprite
                src="/mascot/pet-idle.webp"
                frames={6}
                frameW={144}
                frameH={176}
                height={40}
                paused
                alt="Study buddy"
              />
            </div>
            <span className="companion-title">Study buddy</span>
          </div>
          <button className="companion-collapse" onClick={onClose} aria-label="Collapse" type="button">
            <span aria-hidden>▾</span>
          </button>
        </div>
        <div className="companion-transcript">
          {history.length === 0 && <p className="fine companion-hint">The tutor won’t give you the answer, but it will help you get there.</p>}
          {history.map((item, i) => {
            const isLatest = i === history.length - 1;
            if (item.role === "learner") {
              return (
                <div key={item.id} className="companion-bubble learner">
                  {item.text}
                </div>
              );
            }
            if (item.role === "system") {
              return (
                <div key={item.id} className="companion-bubble system">
                  {item.text}
                </div>
              );
            }
            return (
              <div key={item.id} className="companion-bubble tutor">
                {speaking && isLatest ? (
                  <span>{highlightSpoken(item.text, spokenTo)}</span>
                ) : (
                  <Markdown text={item.text} />
                )}
                {"id" in item && typeof item.id === "string" && item.id && (
                  <FeedbackBar
                    session_id={sessionId}
                    step_id={stepId}
                    target_kind="tutor_message"
                    target_id={item.id}
                  />
                )}
              </div>
            );
          })}
          {busy && (
            <div className="companion-bubble tutor thinking-bubble">
              <Sprite src="/mascot/pet-thinking.webp" frames={6} frameW={144} frameH={176} height={32} loop alt="Thinking" />
              <span className="typing-indicator" aria-label="Study buddy is typing">
                <span />
                <span />
                <span />
              </span>
            </div>
          )}
          <div ref={bottomRef} />
        </div>
        <div className="companion-chips" role="group" aria-label="Card actions">
          <ActionChip
            label="Show a worked example"
            kind="example"
            onClick={() => handleChip("example")}
            disabled={isProbe || busy}
            highlighted={suggestedAction === "example"}
          />
          <ActionChip label="Easier" kind="easier" onClick={() => handleChip("easier")} disabled={isProbe || busy} highlighted={suggestedAction === "easier"} />
          <ActionChip label="Harder" kind="harder" onClick={() => handleChip("harder")} disabled={isProbe || busy} highlighted={suggestedAction === "harder"} />
          <ActionChip
            label="Explain again"
            kind="reexplain"
            onClick={() => handleChip("reexplain")}
            disabled={isProbe || busy}
            highlighted={suggestedAction === "reexplain"}
          />
        </div>
        <form className="companion-input" onSubmit={(e) => { e.preventDefault(); void send(); }}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            maxLength={500}
            placeholder="Ask the tutor..."
            disabled={busy}
            aria-label="Message"
          />
          <button className="btn primary" disabled={busy || !input.trim()} type="submit" data-track="companion.send">
            Send
          </button>
          <button
            type="button"
            className={`btn small${micOn ? " on" : ""}`}
            onClick={toggleMic}
            disabled={!srCtor}
            title={srCtor ? "Voice input" : "Voice input is not supported in this browser"}
            aria-label="Voice input"
            data-track="companion.mic"
          >
            🎤
          </button>
          <button
            type="button"
            className={`btn small${speakerOn ? " on" : ""}`}
            onClick={toggleSpeaker}
            aria-label={speakerOn ? "Turn off read aloud" : "Turn on read aloud"}
            data-track="companion.speaker"
          >
            🔊
          </button>
        </form>
        {view.can_go_back && (
          <div className="companion-back">
            <button className="btn small" onClick={() => void back()} disabled={busy} type="button">
              Back
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function chipLabel(kind: "example" | "easier" | "harder" | "reexplain"): string {
  switch (kind) {
    case "example":
      return "Worked example";
    case "easier":
      return "Easier version";
    case "harder":
      return "Harder version";
    case "reexplain":
      return "Explain again";
  }
}

function ActionChip({
  label,
  kind,
  onClick,
  disabled,
  highlighted,
}: {
  label: string;
  kind: string;
  onClick: () => void;
  disabled: boolean;
  highlighted: boolean;
}) {
  return (
    <button
      type="button"
      className={`chip${highlighted ? " on" : ""}`}
      onClick={onClick}
      disabled={disabled}
      title={disabled ? "Available after you answer" : label}
      data-track={`companion.chip.${kind}`}
    >
      {label}
    </button>
  );
}

function highlightSpoken(text: string, to: number) {
  const end = Math.min(to, text.length);
  return (
    <>
      <span className="spoken">{text.slice(0, end)}</span>
      <span>{text.slice(end)}</span>
    </>
  );
}

function cryptoRandomId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

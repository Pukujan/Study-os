import { useEffect, useState } from "react";
import { browserSpeechAvailable, loadTtsConfig, speakText, type TtsConfig } from "./tts";

export default function VoiceControls({ speakText: text, onTranscript }: { speakText: string; onTranscript: (text: string) => void }) {
  const srCtor =
    typeof window !== "undefined"
      ? (window as unknown as { SpeechRecognition?: unknown; webkitSpeechRecognition?: unknown }).SpeechRecognition ||
        (window as unknown as { SpeechRecognition?: unknown; webkitSpeechRecognition?: unknown }).webkitSpeechRecognition
      : undefined;

  const [note, setNote] = useState<string | null>(null);
  const [tts, setTts] = useState<TtsConfig | null>(null);
  const [speaking, setSpeaking] = useState(false);

  useEffect(() => {
    let cancelled = false;
    loadTtsConfig().then((cfg) => {
      if (!cancelled) setTts(cfg);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const canSpeak = (tts?.engine === "kokoro") || browserSpeechAvailable();

  const speak = () => {
    if (!canSpeak) return;
    setSpeaking(true);
    void speakText(text, {
      onStart: () => setSpeaking(true),
      onEnd: () => setSpeaking(false),
      onError: () => setSpeaking(false),
    });
  };

  const startVoice = () => {
    if (!srCtor) return;
    const rec = new (srCtor as new () => {
      lang: string;
      onresult: ((ev: { results: { transcript: string }[][] }) => void) | null;
      start: () => void;
    })();
    rec.lang = "en-US";
    rec.onresult = (event) => {
      const transcript = event.results[0]?.[0]?.transcript;
      if (transcript) onTranscript(transcript);
    };
    rec.start();
    if (!localStorage.getItem("studyos-voice-noted")) {
      localStorage.setItem("studyos-voice-noted", "1");
      setNote("Voice input uses your browser's speech service.");
    }
  };

  return (
    <div className="voice-controls" role="group" aria-label="Voice controls">
      {canSpeak && (
        <button
          className={`btn small${speaking ? " on" : ""}`}
          onClick={speak}
          aria-label={speaking ? "Speaking" : "Read aloud"}
          data-track="voice.speak"
          type="button"
        >
          🔊
        </button>
      )}
      {!!srCtor && (
        <button className="btn small" onClick={startVoice} aria-label="Voice input" data-track="voice.mic" type="button">
          🎤
        </button>
      )}
      {note && <p className="fine voice-note">{note}</p>}
    </div>
  );
}

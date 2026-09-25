import { useState } from "react";

export default function VoiceControls({ speakText, onTranscript }: { speakText: string; onTranscript: (text: string) => void }) {
  const synth = typeof window !== "undefined" ? window.speechSynthesis : undefined;
  const srCtor = typeof window !== "undefined" ? (window as unknown as { SpeechRecognition?: unknown; webkitSpeechRecognition?: unknown }).SpeechRecognition || (window as unknown as { SpeechRecognition?: unknown; webkitSpeechRecognition?: unknown }).webkitSpeechRecognition : undefined;

  const [note, setNote] = useState<string | null>(null);

  const speak = () => {
    if (!synth) return;
    const u = new SpeechSynthesisUtterance(speakText);
    window.speechSynthesis.speak(u);
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
      const text = event.results[0]?.[0]?.transcript;
      if (text) onTranscript(text);
    };
    rec.start();
    if (!localStorage.getItem("studyos-voice-noted")) {
      localStorage.setItem("studyos-voice-noted", "1");
      setNote("Voice input uses your browser's speech service.");
    }
  };

  return (
    <div className="voice-controls" role="group" aria-label="Voice controls">
      {!!synth && (
        <button className="btn small" onClick={speak} aria-label="Read aloud" data-track="voice.speak" type="button">
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

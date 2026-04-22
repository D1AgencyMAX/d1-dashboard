"use client";

import { useEffect, useRef, useState } from "react";

type Turn = { role: "user" | "assistant"; content: string; audioUrl?: string };
type Stats = {
  totalCost: number;
  totalInputTokens: number;
  totalOutputTokens: number;
  lastLatencyMs: number;
};

// Web Speech API — declared minimally. Chrome/Edge/Safari only.
type SpeechRecognitionLike = {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start: () => void;
  stop: () => void;
  onresult: ((e: { results: { isFinal: boolean; 0: { transcript: string } }[] & { length: number } }) => void) | null;
  onend: (() => void) | null;
  onerror: ((e: { error?: string }) => void) | null;
};

function getSpeechRecognition(): (new () => SpeechRecognitionLike) | null {
  if (typeof window === "undefined") return null;
  const w = window as unknown as {
    SpeechRecognition?: new () => SpeechRecognitionLike;
    webkitSpeechRecognition?: new () => SpeechRecognitionLike;
  };
  return w.SpeechRecognition || w.webkitSpeechRecognition || null;
}

export default function PlaygroundPage() {
  const [history, setHistory] = useState<Turn[]>([]);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [characterDropped, setCharacterDropped] = useState(false);
  const [voiceMode, setVoiceMode] = useState(true);
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(false);
  const [stats, setStats] = useState<Stats>({
    totalCost: 0,
    totalInputTokens: 0,
    totalOutputTokens: 0,
    lastLatencyMs: 0,
  });
  const bottomRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const historyRef = useRef<Turn[]>([]);

  useEffect(() => {
    historyRef.current = history;
  }, [history]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history, loading]);

  useEffect(() => {
    const Ctor = getSpeechRecognition();
    setSpeechSupported(!!Ctor);
    if (!Ctor) return;
    const rec = new Ctor();
    rec.continuous = false;
    rec.interimResults = false;
    rec.lang = "en-AU";
    rec.onresult = (e) => {
      const transcript = Array.from(
        { length: e.results.length },
        (_, i) => (e.results[i] as { isFinal: boolean; 0: { transcript: string } })[0].transcript,
      ).join(" ");
      const finalText = transcript.trim();
      setListening(false);
      if (finalText) {
        void send(finalText);
      }
    };
    rec.onend = () => setListening(false);
    rec.onerror = (ev) => {
      setListening(false);
      if (ev?.error && ev.error !== "no-speech" && ev.error !== "aborted") {
        setError(`mic error: ${ev.error}`);
      }
    };
    recognitionRef.current = rec;
    return () => {
      try {
        rec.stop();
      } catch {
        /* ignore */
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function playTts(text: string): Promise<string | null> {
    try {
      const res = await fetch("/api/playground/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      if (!res.ok) {
        const j = await res.json().catch(() => ({}));
        setError(`voice failed: ${j.error ?? res.status}`);
        return null;
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      if (audioRef.current) {
        audioRef.current.src = url;
        setSpeaking(true);
        audioRef.current.onended = () => setSpeaking(false);
        audioRef.current.onerror = () => setSpeaking(false);
        try {
          await audioRef.current.play();
        } catch {
          // Autoplay blocked. User will see the <audio> controls instead.
          setSpeaking(false);
        }
      }
      return url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "tts failed");
      return null;
    }
  }

  async function send(overrideText?: string) {
    const text = (overrideText ?? draft).trim();
    if (!text || loading) return;
    setError(null);
    setDraft("");
    const nextHistory = [...historyRef.current, { role: "user", content: text } as Turn];
    setHistory(nextHistory);
    setLoading(true);
    try {
      const res = await fetch("/api/playground/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          history: historyRef.current.map((t) => ({ role: t.role, content: t.content })),
          userMessage: text,
        }),
      });
      const json = await res.json();
      if (!res.ok) {
        setError(json.error ?? "failed");
        return;
      }
      const reply = (json.text as string) ?? "(no reply)";
      let audioUrl: string | undefined;
      if (voiceMode && reply) {
        const url = await playTts(reply);
        if (url) audioUrl = url;
      }
      setHistory((prev) => [...prev, { role: "assistant", content: reply, audioUrl }]);
      setStats((s) => ({
        totalCost: Number((s.totalCost + (json.costUsd ?? 0)).toFixed(6)),
        totalInputTokens: s.totalInputTokens + (json.inputTokens ?? 0),
        totalOutputTokens: s.totalOutputTokens + (json.outputTokens ?? 0),
        lastLatencyMs: json.latencyMs ?? 0,
      }));
      if (json.shouldEndCharacter) setCharacterDropped(true);
    } finally {
      setLoading(false);
    }
  }

  function toggleMic() {
    if (!recognitionRef.current || characterDropped) return;
    if (listening) {
      recognitionRef.current.stop();
      return;
    }
    try {
      setError(null);
      recognitionRef.current.start();
      setListening(true);
    } catch {
      // already started, ignore
    }
  }

  function reset() {
    setHistory([]);
    historyRef.current = [];
    setCharacterDropped(false);
    setStats({ totalCost: 0, totalInputTokens: 0, totalOutputTokens: 0, lastLatencyMs: 0 });
    setError(null);
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.src = "";
    }
  }

  return (
    <main className="mx-auto flex min-h-[calc(100vh-3rem)] max-w-3xl flex-col gap-4 px-4 py-6 sm:px-6">
      <header className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-white/10 bg-white/5 p-4">
        <div>
          <h1 className="text-lg font-semibold text-white">🔧 Bruno Papadopoulos</h1>
          <p className="text-xs text-slate-400">
            Local playground. Voice mode uses your browser mic + ElevenLabs for audio replies.
          </p>
        </div>
        <div className="flex items-center gap-3 text-xs text-slate-400">
          <label className="flex items-center gap-1.5 text-white">
            <input
              type="checkbox"
              checked={voiceMode}
              onChange={(e) => setVoiceMode(e.target.checked)}
              className="h-4 w-4 accent-cyan-400"
            />
            Voice mode
          </label>
          <span className="hidden sm:inline">
            ${stats.totalCost.toFixed(4)} · in {stats.totalInputTokens} · out{" "}
            {stats.totalOutputTokens}
            {stats.lastLatencyMs ? ` · ${stats.lastLatencyMs}ms` : ""}
          </span>
          <button
            onClick={reset}
            className="rounded-full bg-white/10 px-3 py-1 text-white hover:bg-white/20"
          >
            Reset
          </button>
        </div>
      </header>

      {characterDropped ? (
        <div className="rounded-xl border border-amber-400/30 bg-amber-400/10 px-4 py-3 text-sm text-amber-100">
          Bruno dropped character (safety sentinel). Reset to try again.
        </div>
      ) : null}

      {voiceMode && !speechSupported ? (
        <div className="rounded-xl border border-rose-400/30 bg-rose-400/10 px-4 py-3 text-sm text-rose-100">
          Your browser doesn&apos;t expose the Web Speech API. Use Chrome, Edge, or Safari — or
          turn off Voice mode and type instead.
        </div>
      ) : null}

      <section className="flex-1 space-y-2 overflow-y-auto rounded-2xl border border-white/10 bg-slate-950/50 p-4">
        {history.length === 0 ? (
          <p className="text-sm text-slate-500">
            {voiceMode
              ? "Tap the 🎤 and say something. Bruno will reply out loud."
              : "Start the conversation. Try \"mate is this the tyre shop\"."}
          </p>
        ) : (
          history.map((t, i) => <Bubble key={i} turn={t} />)
        )}
        {loading ? (
          <div className="flex justify-start">
            <div className="rounded-2xl bg-cyan-500/10 px-4 py-2 text-sm text-cyan-200">
              <span className="inline-flex gap-1">
                <span className="animate-bounce">.</span>
                <span className="animate-bounce [animation-delay:120ms]">.</span>
                <span className="animate-bounce [animation-delay:240ms]">.</span>
              </span>
            </div>
          </div>
        ) : null}
        <div ref={bottomRef} />
      </section>

      {error ? (
        <p className="rounded-lg bg-rose-500/10 px-3 py-2 text-sm text-rose-200">{error}</p>
      ) : null}

      <div className="flex items-center gap-2">
        {voiceMode && speechSupported ? (
          <button
            type="button"
            onClick={toggleMic}
            disabled={loading || characterDropped}
            className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-lg transition ${
              listening
                ? "bg-rose-500 text-white ring-2 ring-rose-300 ring-offset-2 ring-offset-slate-950"
                : "bg-cyan-500 text-slate-950 hover:bg-cyan-400"
            } disabled:opacity-40`}
            title={listening ? "Stop listening" : "Hold or tap to speak"}
            aria-label={listening ? "Stop listening" : "Speak"}
          >
            {listening ? "■" : "🎤"}
          </button>
        ) : null}
        <form
          className="flex flex-1 gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            send();
          }}
        >
          <input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder={listening ? "Listening…" : "Type like you are the target…"}
            disabled={loading || characterDropped || listening}
            className="flex-1 rounded-full border border-white/10 bg-slate-950/60 px-4 py-2 text-white placeholder:text-slate-600 disabled:opacity-40"
            autoFocus
          />
          <button
            type="submit"
            disabled={loading || !draft.trim() || characterDropped}
            className="rounded-full bg-cyan-500 px-5 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-40"
          >
            Send
          </button>
        </form>
      </div>

      <audio ref={audioRef} className="hidden" />
      {speaking ? (
        <p className="text-center text-xs text-cyan-300/80">Bruno is speaking…</p>
      ) : null}
    </main>
  );
}

function Bubble({ turn }: { turn: Turn }) {
  const fromBot = turn.role === "assistant";
  return (
    <div className={`flex ${fromBot ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] space-y-1 whitespace-pre-wrap rounded-2xl px-4 py-2 text-sm ${
          fromBot
            ? "bg-cyan-500/15 text-cyan-50 ring-1 ring-cyan-400/20"
            : "bg-white/10 text-slate-100"
        }`}
      >
        <p>{turn.content}</p>
        {turn.audioUrl ? (
          <audio controls src={turn.audioUrl} className="w-full pt-1" />
        ) : null}
      </div>
    </div>
  );
}

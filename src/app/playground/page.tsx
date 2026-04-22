"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type Turn = { role: "user" | "assistant"; content: string; audioUrl?: string };
type Phase = "idle" | "listening" | "thinking" | "speaking";
type Stats = {
  brainCost: number;
  voiceCost: number;
  voiceChars: number;
  totalInputTokens: number;
  totalOutputTokens: number;
  lastLatencyMs: number;
};

// ElevenLabs pay-as-you-go pricing reference: used only for display; the
// authoritative number is on elevenlabs.io/app/usage.
const ELEVENLABS_PRICE_PER_1K_CHARS = 0.3;

// Web Speech API — declared minimally. Chrome/Edge/Safari only.
type SpeechRecognitionLike = {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onresult:
    | ((e: {
        results: { isFinal: boolean; 0: { transcript: string } }[] & { length: number };
      }) => void)
    | null;
  onend: (() => void) | null;
  onstart: (() => void) | null;
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
  const [phase, setPhase] = useState<Phase>("idle");
  const [conversationActive, setConversationActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [characterDropped, setCharacterDropped] = useState(false);
  const [voiceMode, setVoiceMode] = useState(true);
  const [speechSupported, setSpeechSupported] = useState(false);
  const [stats, setStats] = useState<Stats>({
    brainCost: 0,
    voiceCost: 0,
    voiceChars: 0,
    totalInputTokens: 0,
    totalOutputTokens: 0,
    lastLatencyMs: 0,
  });
  const bottomRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const historyRef = useRef<Turn[]>([]);
  // Async callbacks (TTS onended, recognition onend) need the latest values,
  // but setState closures capture stale ones. Refs bridge the gap.
  const conversationActiveRef = useRef(false);
  const phaseRef = useRef<Phase>("idle");
  const characterDroppedRef = useRef(false);

  useEffect(() => {
    historyRef.current = history;
  }, [history]);
  useEffect(() => {
    conversationActiveRef.current = conversationActive;
  }, [conversationActive]);
  useEffect(() => {
    phaseRef.current = phase;
  }, [phase]);
  useEffect(() => {
    characterDroppedRef.current = characterDropped;
  }, [characterDropped]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history, phase]);

  // --- Recognition helpers -------------------------------------------------
  const startListening = useCallback(() => {
    const rec = recognitionRef.current;
    if (!rec) return;
    if (phaseRef.current === "listening") return;
    if (characterDroppedRef.current) return;
    try {
      setError(null);
      rec.start();
    } catch {
      // Some browsers throw if start() is called while already in a start
      // state. onend will fire; the loop will self-heal.
    }
  }, []);

  const stopListening = useCallback(() => {
    try {
      recognitionRef.current?.stop();
    } catch {
      /* ignore */
    }
  }, []);

  // --- TTS -----------------------------------------------------------------
  const speakLocally = useCallback((text: string, onDone: () => void) => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      onDone();
      return;
    }
    try {
      window.speechSynthesis.cancel();
      const utter = new SpeechSynthesisUtterance(text);
      utter.lang = "en-AU";
      utter.rate = 1.0;
      utter.pitch = 0.85;
      const voices = window.speechSynthesis.getVoices();
      const preferred =
        voices.find((v) => /en-AU/i.test(v.lang) && /Male|Karen|Lee/i.test(v.name)) ||
        voices.find((v) => /en-AU/i.test(v.lang)) ||
        voices.find((v) => /en-GB/i.test(v.lang));
      if (preferred) utter.voice = preferred;
      utter.onend = () => onDone();
      utter.onerror = () => onDone();
      window.speechSynthesis.speak(utter);
    } catch {
      onDone();
    }
  }, []);

  const playTts = useCallback(
    async (text: string, onDone: () => void): Promise<string | null> => {
      try {
        const res = await fetch("/api/playground/tts", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text }),
        });
        if (!res.ok) {
          const j = await res.json().catch(() => ({}));
          const reason = j.error ?? String(res.status);
          setError(`ElevenLabs unreachable (${reason}). Using browser voice fallback.`);
          speakLocally(text, onDone);
          return null;
        }
        const costHeader = res.headers.get("X-Cost-Usd");
        const cost = costHeader
          ? Number(costHeader)
          : (text.length / 1000) * ELEVENLABS_PRICE_PER_1K_CHARS;
        setStats((s) => ({
          ...s,
          voiceCost: Number((s.voiceCost + (isFinite(cost) ? cost : 0)).toFixed(6)),
          voiceChars: s.voiceChars + text.length,
        }));
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const audio = audioRef.current;
        if (!audio) {
          onDone();
          return null;
        }
        audio.src = url;
        const finish = () => {
          audio.onended = null;
          audio.onerror = null;
          onDone();
        };
        audio.onended = finish;
        audio.onerror = finish;
        try {
          await audio.play();
        } catch {
          // Autoplay blocked. Finish so the loop moves on.
          finish();
        }
        return url;
      } catch (err) {
        setError(err instanceof Error ? err.message : "tts failed");
        speakLocally(text, onDone);
        return null;
      }
    },
    [speakLocally],
  );

  // --- Sending a turn ------------------------------------------------------
  const send = useCallback(
    async (overrideText?: string) => {
      const text = (overrideText ?? draft).trim();
      if (!text) return;
      if (phaseRef.current === "thinking" || phaseRef.current === "speaking") return;
      setError(null);
      setDraft("");
      setPhase("thinking");
      const nextHistory = [...historyRef.current, { role: "user", content: text } as Turn];
      setHistory(nextHistory);
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
          setPhase("idle");
          return;
        }
        const reply = (json.text as string) ?? "(no reply)";
        setStats((s) => ({
          ...s,
          brainCost: Number((s.brainCost + (json.costUsd ?? 0)).toFixed(6)),
          totalInputTokens: s.totalInputTokens + (json.inputTokens ?? 0),
          totalOutputTokens: s.totalOutputTokens + (json.outputTokens ?? 0),
          lastLatencyMs: json.latencyMs ?? 0,
        }));
        if (json.shouldEndCharacter) {
          setCharacterDropped(true);
          setConversationActive(false);
        }

        // The onDone callback is what closes the turn and optionally reopens
        // the mic for continuous conversation.
        const onTurnComplete = () => {
          setPhase("idle");
          if (
            conversationActiveRef.current &&
            !characterDroppedRef.current &&
            recognitionRef.current
          ) {
            // Small delay so the browser releases the audio element's mic
            // contention before we re-start recognition.
            setTimeout(() => {
              if (conversationActiveRef.current && phaseRef.current === "idle") {
                setPhase("listening");
                startListening();
              }
            }, 250);
          }
        };

        let audioUrl: string | undefined;
        if (voiceMode && reply) {
          setPhase("speaking");
          const url = await playTts(reply, onTurnComplete);
          if (url) audioUrl = url;
        } else {
          onTurnComplete();
        }
        setHistory((prev) => [...prev, { role: "assistant", content: reply, audioUrl }]);
      } catch (err) {
        setError(err instanceof Error ? err.message : "send failed");
        setPhase("idle");
      }
    },
    [draft, voiceMode, playTts, startListening],
  );

  // --- Mount: wire up recognition ------------------------------------------
  useEffect(() => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.getVoices();
      window.speechSynthesis.onvoiceschanged = () => {
        window.speechSynthesis.getVoices();
      };
    }
    const Ctor = getSpeechRecognition();
    setSpeechSupported(!!Ctor);
    if (!Ctor) return;
    const rec = new Ctor();
    rec.continuous = false;
    rec.interimResults = false;
    rec.lang = "en-AU";
    rec.onstart = () => setPhase("listening");
    rec.onresult = (e) => {
      const transcript = Array.from(
        { length: e.results.length },
        (_, i) => (e.results[i] as { isFinal: boolean; 0: { transcript: string } })[0].transcript,
      ).join(" ");
      const finalText = transcript.trim();
      if (finalText) {
        void send(finalText);
      } else {
        setPhase("idle");
      }
    };
    rec.onend = () => {
      // If recognition ended without a result (silence / no-speech),
      // drop to idle. The TTS callback (or the user) will restart it if
      // conversation mode is still on.
      if (phaseRef.current === "listening") setPhase("idle");
      // In continuous mode, if no result fired and we didn't transition to
      // thinking, retry after a beat so the user doesn't have to tap again.
      if (
        conversationActiveRef.current &&
        phaseRef.current === "idle" &&
        !characterDroppedRef.current
      ) {
        setTimeout(() => {
          if (conversationActiveRef.current && phaseRef.current === "idle") {
            startListening();
          }
        }, 400);
      }
    };
    rec.onerror = (ev) => {
      setPhase("idle");
      const err = ev?.error;
      if (err && err !== "no-speech" && err !== "aborted") {
        setError(`mic error: ${err}`);
        setConversationActive(false);
      }
    };
    recognitionRef.current = rec;
    return () => {
      try {
        rec.abort();
      } catch {
        /* ignore */
      }
    };
  }, [send, startListening]);

  // --- Conversation control -----------------------------------------------
  function startConversation() {
    if (!recognitionRef.current || characterDroppedRef.current) return;
    setError(null);
    setConversationActive(true);
    startListening();
  }

  function stopConversation() {
    setConversationActive(false);
    conversationActiveRef.current = false;
    stopListening();
    if (audioRef.current) {
      audioRef.current.pause();
    }
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    setPhase("idle");
  }

  function reset() {
    stopConversation();
    setHistory([]);
    historyRef.current = [];
    setCharacterDropped(false);
    setStats({
      brainCost: 0,
      voiceCost: 0,
      voiceChars: 0,
      totalInputTokens: 0,
      totalOutputTokens: 0,
      lastLatencyMs: 0,
    });
    setError(null);
  }

  const phaseLabel: Record<Phase, string> = {
    idle: "Idle",
    listening: "Listening…",
    thinking: "Bruno is thinking…",
    speaking: "Bruno is speaking…",
  };
  const phaseColor: Record<Phase, string> = {
    idle: "text-slate-400",
    listening: "text-rose-300",
    thinking: "text-amber-300",
    speaking: "text-cyan-300",
  };
  const thinking = phase === "thinking";

  return (
    <main className="mx-auto flex min-h-[calc(100vh-3rem)] max-w-3xl flex-col gap-4 px-4 py-6 sm:px-6">
      <header className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-white/10 bg-white/5 p-4">
        <div>
          <h1 className="text-lg font-semibold text-white">🔧 Bruno Papadopoulos</h1>
          <p className="text-xs text-slate-400">
            Hit <span className="font-semibold text-white">Start talking</span> to have a real
            back-and-forth. Bruno listens, thinks, speaks, then opens the mic again.
          </p>
        </div>
        <div className="flex items-center gap-3 text-xs text-slate-400">
          <label className="flex items-center gap-1.5 text-white">
            <input
              type="checkbox"
              checked={voiceMode}
              onChange={(e) => setVoiceMode(e.target.checked)}
              className="h-4 w-4 accent-cyan-400"
              disabled={conversationActive}
            />
            Voice mode
          </label>
          <span className="hidden sm:inline">
            brain ${stats.brainCost.toFixed(4)} · voice ${stats.voiceCost.toFixed(4)} (
            {stats.voiceChars}ch)
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
              ? "Click Start talking and just speak. Pause when you're done and Bruno will reply."
              : 'Type something like "mate is this the tyre shop".'}
          </p>
        ) : (
          history.map((t, i) => <Bubble key={i} turn={t} />)
        )}
        {thinking ? (
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

      {voiceMode && speechSupported ? (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-white/10 bg-white/5 p-3">
          <div className="flex items-center gap-3">
            <PhaseDot phase={phase} />
            <span className={`text-sm font-medium ${phaseColor[phase]}`}>
              {phaseLabel[phase]}
            </span>
          </div>
          {conversationActive ? (
            <button
              onClick={stopConversation}
              className="rounded-full bg-rose-500 px-5 py-2 text-sm font-semibold text-white hover:bg-rose-400"
            >
              ■ Stop
            </button>
          ) : (
            <button
              onClick={startConversation}
              disabled={characterDropped}
              className="rounded-full bg-cyan-500 px-5 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-40"
            >
              🎤 Start talking
            </button>
          )}
        </div>
      ) : null}

      <form
        className="flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          void send();
        }}
      >
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={
            phase === "listening"
              ? "Listening…"
              : phase === "thinking"
              ? "Bruno is thinking…"
              : phase === "speaking"
              ? "Bruno is speaking…"
              : "Or type like you are the target…"
          }
          disabled={
            phase === "listening" ||
            phase === "thinking" ||
            phase === "speaking" ||
            characterDropped
          }
          className="flex-1 rounded-full border border-white/10 bg-slate-950/60 px-4 py-2 text-white placeholder:text-slate-600 disabled:opacity-40"
        />
        <button
          type="submit"
          disabled={phase !== "idle" || !draft.trim() || characterDropped}
          className="rounded-full bg-cyan-500 px-5 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-40"
        >
          Send
        </button>
      </form>

      <audio ref={audioRef} className="hidden" />
    </main>
  );
}

function PhaseDot({ phase }: { phase: Phase }) {
  const color =
    phase === "listening"
      ? "bg-rose-400"
      : phase === "thinking"
      ? "bg-amber-400"
      : phase === "speaking"
      ? "bg-cyan-400"
      : "bg-slate-500";
  const pulse = phase !== "idle" ? "animate-pulse" : "";
  return <span className={`h-3 w-3 rounded-full ${color} ${pulse}`} />;
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

"use client";

import { useEffect, useRef, useState } from "react";

type Turn = { role: "user" | "assistant"; content: string };
type Stats = {
  totalCost: number;
  totalInputTokens: number;
  totalOutputTokens: number;
  lastLatencyMs: number;
};

export default function PlaygroundPage() {
  const [history, setHistory] = useState<Turn[]>([]);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [characterDropped, setCharacterDropped] = useState(false);
  const [stats, setStats] = useState<Stats>({
    totalCost: 0,
    totalInputTokens: 0,
    totalOutputTokens: 0,
    lastLatencyMs: 0,
  });
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history, loading]);

  async function send() {
    const text = draft.trim();
    if (!text || loading) return;
    setError(null);
    setDraft("");
    const nextHistory = [...history, { role: "user", content: text } as Turn];
    setHistory(nextHistory);
    setLoading(true);
    try {
      const res = await fetch("/api/playground/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ history, userMessage: text }),
      });
      const json = await res.json();
      if (!res.ok) {
        setError(json.error ?? "failed");
        return;
      }
      const reply = (json.text as string) ?? "(no reply)";
      setHistory([...nextHistory, { role: "assistant", content: reply }]);
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

  function reset() {
    setHistory([]);
    setCharacterDropped(false);
    setStats({ totalCost: 0, totalInputTokens: 0, totalOutputTokens: 0, lastLatencyMs: 0 });
    setError(null);
  }

  return (
    <main className="mx-auto flex min-h-[calc(100vh-3rem)] max-w-3xl flex-col gap-4 px-4 py-6 sm:px-6">
      <header className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-white/10 bg-white/5 p-4">
        <div>
          <h1 className="text-lg font-semibold text-white">🔧 Bruno Papadopoulos</h1>
          <p className="text-xs text-slate-400">
            Local playground. No WhatsApp, no DB. Talk to Bruno in the browser to test the
            character.
          </p>
        </div>
        <div className="flex items-center gap-3 text-xs text-slate-400">
          <span>
            ${stats.totalCost.toFixed(4)} · in {stats.totalInputTokens} · out{" "}
            {stats.totalOutputTokens}
            {stats.lastLatencyMs ? ` · last ${stats.lastLatencyMs}ms` : ""}
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

      <section className="flex-1 space-y-2 overflow-y-auto rounded-2xl border border-white/10 bg-slate-950/50 p-4">
        {history.length === 0 ? (
          <p className="text-sm text-slate-500">
            Start the conversation. Try &quot;mate is this the tyre shop&quot; or say something
            that makes Bruno want to argue.
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

      <form
        className="flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          send();
        }}
      >
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Type like you are the target…"
          disabled={loading || characterDropped}
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
    </main>
  );
}

function Bubble({ turn }: { turn: Turn }) {
  const fromBot = turn.role === "assistant";
  return (
    <div className={`flex ${fromBot ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] whitespace-pre-wrap rounded-2xl px-4 py-2 text-sm ${
          fromBot
            ? "bg-cyan-500/15 text-cyan-50 ring-1 ring-cyan-400/20"
            : "bg-white/10 text-slate-100"
        }`}
      >
        {turn.content}
      </div>
    </div>
  );
}

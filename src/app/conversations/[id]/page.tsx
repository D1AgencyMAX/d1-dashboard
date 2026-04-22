"use client";

import { use, useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";
import type { Character, Conversation, Message } from "@/lib/comedian/types";

export default function ConversationDetail({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [convo, setConvo] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [character, setCharacter] = useState<Character | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      const [{ data: c }, { data: ms }] = await Promise.all([
        supabase.from("conversations").select("*").eq("id", id).maybeSingle(),
        supabase
          .from("messages")
          .select("*")
          .eq("conversation_id", id)
          .order("created_at", { ascending: true }),
      ]);
      setConvo((c as Conversation) ?? null);
      setMessages((ms as Message[]) ?? []);
      if (c) {
        const { data: ch } = await supabase
          .from("characters")
          .select("*")
          .eq("id", (c as Conversation).character_id)
          .maybeSingle();
        setCharacter((ch as Character) ?? null);
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    const channel = supabase
      .channel(`conversation-${id}`)
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "messages", filter: `conversation_id=eq.${id}` },
        () => load(),
      )
      .subscribe();
    return () => {
      void supabase.removeChannel(channel);
    };
  }, [id]);

  async function toggleHighlight() {
    if (!convo) return;
    await supabase
      .from("conversations")
      .update({ highlight: !convo.highlight })
      .eq("id", convo.id);
    load();
  }

  async function closeConversation() {
    if (!convo) return;
    await supabase
      .from("conversations")
      .update({ status: "closed", closed_at: new Date().toISOString() })
      .eq("id", convo.id);
    load();
  }

  if (loading) {
    return <main className="mx-auto max-w-4xl px-4 py-8 text-sm text-slate-500">Loading…</main>;
  }
  if (!convo) {
    return <main className="mx-auto max-w-4xl px-4 py-8 text-sm text-slate-500">Not found.</main>;
  }

  const totalCost = messages.reduce((sum, m) => sum + Number(m.cost_usd ?? 0), 0);

  return (
    <main className="mx-auto max-w-4xl space-y-4 px-4 py-8 sm:px-6 lg:px-8">
      <header className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-white/10 bg-white/5 p-5">
        <div>
          <h1 className="text-xl font-semibold text-white">
            {character?.avatar_emoji ?? "🎤"} {convo.contact_profile_name ?? convo.contact_phone}
          </h1>
          <p className="text-xs text-slate-400">
            {character?.name} &middot; {convo.direction} &middot; {convo.status} &middot;{" "}
            {messages.length} messages &middot; ${totalCost.toFixed(4)}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={toggleHighlight}
            className={`rounded-full px-3 py-1.5 text-sm ${
              convo.highlight
                ? "bg-amber-400/20 text-amber-200"
                : "bg-white/10 text-slate-200 hover:bg-white/20"
            }`}
          >
            {convo.highlight ? "★ Highlight" : "☆ Highlight"}
          </button>
          {convo.status === "open" ? (
            <button
              onClick={closeConversation}
              className="rounded-full bg-rose-500/20 px-3 py-1.5 text-sm text-rose-200 hover:bg-rose-500/30"
            >
              Close
            </button>
          ) : null}
        </div>
      </header>

      <ol className="space-y-2">
        {messages.map((m) => (
          <Bubble key={m.id} message={m} />
        ))}
      </ol>
    </main>
  );
}

function Bubble({ message }: { message: Message }) {
  const fromBot = message.direction === "out";
  const isSystem = message.kind === "system";
  const text = message.text ?? message.transcript ?? "";
  const audioSrc = message.audio_path ? `/api/media/${message.id}` : null;
  return (
    <li className={`flex ${fromBot ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] space-y-1 rounded-2xl px-4 py-2 text-sm ${
          isSystem
            ? "bg-slate-800/60 text-slate-400 italic"
            : fromBot
            ? "bg-cyan-500/15 text-cyan-50 ring-1 ring-cyan-400/20"
            : "bg-white/10 text-slate-100"
        }`}
      >
        {text ? <p className="whitespace-pre-wrap">{text}</p> : null}
        {audioSrc ? (
          <audio controls className="w-full">
            <source src={audioSrc} type="audio/ogg" />
          </audio>
        ) : null}
        <p className="text-right text-[10px] uppercase tracking-wider text-slate-500">
          {new Date(message.created_at).toLocaleString("en-AU")}
          {message.latency_ms ? ` · ${message.latency_ms}ms` : ""}
          {message.cost_usd ? ` · $${Number(message.cost_usd).toFixed(4)}` : ""}
        </p>
      </div>
    </li>
  );
}

"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";
import type { Character, Conversation } from "@/lib/comedian/types";

type Row = Conversation & { message_count?: number; last_text?: string };

export default function ConversationsPage() {
  const [rows, setRows] = useState<Row[]>([]);
  const [characters, setCharacters] = useState<Record<string, Character>>({});
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      const [{ data: convos }, { data: chs }] = await Promise.all([
        supabase
          .from("conversations_with_counts")
          .select("*")
          .order("last_message_at", { ascending: false, nullsFirst: false })
          .limit(200),
        supabase.from("characters").select("*"),
      ]);
      setRows((convos ?? []) as Row[]);
      const map: Record<string, Character> = {};
      for (const c of (chs ?? []) as Character[]) map[c.id] = c;
      setCharacters(map);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    const channel = supabase
      .channel("conversations-live")
      .on("postgres_changes", { event: "*", schema: "public", table: "messages" }, () => load())
      .on("postgres_changes", { event: "*", schema: "public", table: "conversations" }, () => load())
      .subscribe();
    return () => {
      void supabase.removeChannel(channel);
    };
  }, []);

  return (
    <main className="mx-auto max-w-6xl space-y-6 px-4 py-8 sm:px-6 lg:px-8">
      <header>
        <h1 className="text-2xl font-semibold text-white">Conversations</h1>
        <p className="mt-1 text-sm text-slate-400">
          Live feed of every WhatsApp thread the comedian is on. Tap a row to see the transcript,
          play voice notes, or mark it as a highlight for your YouTube clips library.
        </p>
      </header>

      {loading ? (
        <p className="text-sm text-slate-500">Loading…</p>
      ) : rows.length === 0 ? (
        <p className="text-sm text-slate-500">
          No conversations yet. Once someone messages your WhatsApp Business number, threads will
          appear here.
        </p>
      ) : (
        <ul className="space-y-3">
          {rows.map((r) => {
            const ch = characters[r.character_id];
            return (
              <li key={r.id}>
                <Link
                  href={`/conversations/${r.id}`}
                  className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-white/10 bg-white/5 p-4 transition hover:border-cyan-400/30 hover:bg-white/10"
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xl">{ch?.avatar_emoji ?? "🎤"}</span>
                      <p className="font-medium text-white">
                        {r.contact_profile_name ?? r.contact_phone}
                      </p>
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs ${
                          r.direction === "inbound"
                            ? "bg-emerald-500/15 text-emerald-300"
                            : "bg-sky-500/15 text-sky-300"
                        }`}
                      >
                        {r.direction}
                      </span>
                      {r.highlight ? (
                        <span className="rounded-full bg-amber-400/15 px-2 py-0.5 text-xs text-amber-200">
                          highlight
                        </span>
                      ) : null}
                    </div>
                    <p className="mt-1 truncate text-sm text-slate-400">
                      {r.last_text || `${r.message_count ?? 0} messages`}
                    </p>
                  </div>
                  <div className="text-right text-xs text-slate-500">
                    <p>{ch?.name ?? "—"}</p>
                    <p>
                      {r.last_message_at
                        ? new Date(r.last_message_at).toLocaleString("en-AU")
                        : "—"}
                    </p>
                  </div>
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </main>
  );
}

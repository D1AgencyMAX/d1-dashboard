"use client";

import { useEffect, useState } from "react";
import type { Character } from "@/lib/comedian/types";

export default function CharactersPage() {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<Character | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try {
      const r = await fetch("/api/characters");
      const j = await r.json();
      setCharacters(Array.isArray(j) ? j : []);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function save() {
    if (!editing) return;
    setError(null);
    const isNew = !editing.id;
    const res = await fetch(isNew ? "/api/characters" : `/api/characters/${editing.id}`, {
      method: isNew ? "POST" : "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(editing),
    });
    if (!res.ok) {
      const j = await res.json().catch(() => ({}));
      setError(j.error ?? "save failed");
      return;
    }
    setEditing(null);
    load();
  }

  async function remove(id: string) {
    if (!confirm("Delete this character? Conversations that reference it will be kept but orphaned.")) return;
    const res = await fetch(`/api/characters/${id}`, { method: "DELETE" });
    if (!res.ok) {
      const j = await res.json().catch(() => ({}));
      alert(j.error ?? "delete failed");
      return;
    }
    load();
  }

  return (
    <main className="mx-auto max-w-6xl space-y-6 px-4 py-8 sm:px-6 lg:px-8">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-white">Characters</h1>
          <p className="mt-1 text-sm text-slate-400">
            The persona that talks to targets on WhatsApp. The system prompt is what the model
            sees; voice ID comes from ElevenLabs.
          </p>
        </div>
        <button
          onClick={() =>
            setEditing({
              id: "",
              slug: "",
              name: "",
              tagline: "",
              system_prompt: "",
              style_notes: "",
              voice_provider: "elevenlabs",
              voice_id: "",
              model: "claude-sonnet-4-6",
              temperature: 0.9,
              max_output_tokens: 320,
              avatar_emoji: "🎤",
              is_active: true,
              created_at: "",
              updated_at: "",
            } as Character)
          }
          className="rounded-full bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400"
        >
          + New character
        </button>
      </header>

      {loading ? (
        <p className="text-sm text-slate-500">Loading…</p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {characters.map((c) => (
            <article key={c.id} className="flex flex-col rounded-2xl border border-white/10 bg-white/5 p-5">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2 text-lg font-semibold text-white">
                    <span className="text-2xl">{c.avatar_emoji ?? "🎤"}</span>
                    {c.name}
                  </div>
                  <p className="text-xs uppercase tracking-wider text-slate-500">{c.slug}</p>
                </div>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs ${
                    c.is_active ? "bg-emerald-500/15 text-emerald-300" : "bg-slate-600/30 text-slate-400"
                  }`}
                >
                  {c.is_active ? "active" : "inactive"}
                </span>
              </div>
              {c.tagline ? <p className="mt-2 text-sm text-slate-300">{c.tagline}</p> : null}
              <p className="mt-3 line-clamp-5 whitespace-pre-wrap text-xs text-slate-400">
                {c.system_prompt.slice(0, 400)}
                {c.system_prompt.length > 400 ? "…" : ""}
              </p>
              <div className="mt-4 flex items-center justify-between text-xs text-slate-500">
                <span>
                  {c.model} &middot; temp {c.temperature}
                </span>
                <div className="flex gap-2">
                  <button
                    onClick={() => setEditing(c)}
                    className="rounded-full bg-white/10 px-3 py-1 text-white hover:bg-white/20"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => remove(c.id)}
                    className="rounded-full bg-rose-500/20 px-3 py-1 text-rose-200 hover:bg-rose-500/30"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}

      {editing ? (
        <div
          className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-slate-950/80 px-4 py-10"
          onClick={() => setEditing(null)}
        >
          <div
            className="w-full max-w-3xl space-y-3 rounded-2xl border border-white/10 bg-slate-900 p-6 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-lg font-semibold text-white">
              {editing.id ? "Edit character" : "New character"}
            </h2>
            <div className="grid gap-3 sm:grid-cols-2">
              <Input
                label="Slug"
                value={editing.slug}
                onChange={(v) => setEditing({ ...editing, slug: v })}
              />
              <Input
                label="Name"
                value={editing.name}
                onChange={(v) => setEditing({ ...editing, name: v })}
              />
              <Input
                label="Tagline"
                value={editing.tagline ?? ""}
                onChange={(v) => setEditing({ ...editing, tagline: v })}
              />
              <Input
                label="Avatar emoji"
                value={editing.avatar_emoji ?? ""}
                onChange={(v) => setEditing({ ...editing, avatar_emoji: v })}
              />
              <Input
                label="Voice ID (ElevenLabs)"
                value={editing.voice_id ?? ""}
                onChange={(v) => setEditing({ ...editing, voice_id: v })}
              />
              <label className="flex flex-col text-sm text-slate-300">
                Model
                <select
                  value={editing.model}
                  onChange={(e) => setEditing({ ...editing, model: e.target.value })}
                  className="mt-1 rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-white"
                >
                  <option value="claude-sonnet-4-6">claude-sonnet-4-6</option>
                  <option value="claude-opus-4-7">claude-opus-4-7</option>
                  <option value="claude-haiku-4-5-20251001">claude-haiku-4-5</option>
                </select>
              </label>
              <Input
                label="Temperature"
                value={String(editing.temperature)}
                onChange={(v) => setEditing({ ...editing, temperature: Number(v) || 0 })}
              />
              <Input
                label="Max output tokens"
                value={String(editing.max_output_tokens)}
                onChange={(v) => setEditing({ ...editing, max_output_tokens: Number(v) || 0 })}
              />
            </div>
            <label className="flex flex-col text-sm text-slate-300">
              System prompt
              <textarea
                value={editing.system_prompt}
                onChange={(e) => setEditing({ ...editing, system_prompt: e.target.value })}
                rows={16}
                className="mt-1 rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 font-mono text-xs text-white"
              />
            </label>
            <label className="flex items-center gap-2 text-sm text-slate-300">
              <input
                type="checkbox"
                checked={editing.is_active}
                onChange={(e) => setEditing({ ...editing, is_active: e.target.checked })}
              />
              Active
            </label>
            {error ? <p className="text-sm text-rose-300">{error}</p> : null}
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setEditing(null)}
                className="rounded-full bg-white/10 px-4 py-2 text-sm text-white hover:bg-white/20"
              >
                Cancel
              </button>
              <button
                onClick={save}
                className="rounded-full bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </main>
  );
}

function Input({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <label className="flex flex-col text-sm text-slate-300">
      {label}
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-white"
      />
    </label>
  );
}

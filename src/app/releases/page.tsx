"use client";

import { useEffect, useState } from "react";
import type { Character, OutboundRelease, WaNumber } from "@/lib/comedian/types";

export default function ReleasesPage() {
  const [releases, setReleases] = useState<OutboundRelease[]>([]);
  const [numbers, setNumbers] = useState<WaNumber[]>([]);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({
    target_phone: "",
    target_name: "",
    signer_name: "",
    signer_relationship: "",
    signer_signature: "",
    notes: "",
  });
  const [launch, setLaunch] = useState({
    wa_number_id: "",
    character_id: "",
    target_phone: "",
    template_name: "",
    language_code: "en_US",
  });
  const [error, setError] = useState<string | null>(null);
  const [launchError, setLaunchError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try {
      const [r, n, c] = await Promise.all([
        fetch("/api/releases").then((res) => res.json()),
        fetch("/api/numbers").then((res) => res.json()),
        fetch("/api/characters").then((res) => res.json()),
      ]);
      setReleases(Array.isArray(r) ? r : []);
      setNumbers(Array.isArray(n) ? n : []);
      setCharacters(Array.isArray(c) ? c : []);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const res = await fetch("/api/releases", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });
    if (!res.ok) {
      const j = await res.json().catch(() => ({}));
      setError(j.error ?? "failed");
      return;
    }
    setForm({
      target_phone: "",
      target_name: "",
      signer_name: "",
      signer_relationship: "",
      signer_signature: "",
      notes: "",
    });
    load();
  }

  async function startConversation(e: React.FormEvent) {
    e.preventDefault();
    setLaunchError(null);
    const res = await fetch("/api/whatsapp/outbound", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(launch),
    });
    const j = await res.json().catch(() => ({}));
    if (!res.ok) {
      setLaunchError(j.error ?? "launch failed");
      return;
    }
    setLaunchError(null);
    alert(`Template sent. Conversation id: ${j.conversation_id}`);
  }

  return (
    <main className="mx-auto max-w-6xl space-y-8 px-4 py-8 sm:px-6 lg:px-8">
      <header>
        <h1 className="text-2xl font-semibold text-white">Outbound releases</h1>
        <p className="mt-1 text-sm text-slate-400">
          Before the bot can message a target first, someone who knows them has to sign a release
          here. The signer&apos;s typed name + signature string are the legal consent on file. A
          valid release is required for every outbound send.
        </p>
      </header>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
            Record a signed release
          </h2>
          <form onSubmit={submit} className="mt-4 space-y-3">
            <Input
              label="Target phone (international format)"
              value={form.target_phone}
              onChange={(v) => setForm({ ...form, target_phone: v })}
              placeholder="+61412345678"
            />
            <Input
              label="Target name"
              value={form.target_name}
              onChange={(v) => setForm({ ...form, target_name: v })}
              placeholder="Stav the Cousin"
            />
            <Input
              label="Signer name"
              value={form.signer_name}
              onChange={(v) => setForm({ ...form, signer_name: v })}
              placeholder="Nick Papadopoulos"
            />
            <Input
              label="Relationship to target"
              value={form.signer_relationship}
              onChange={(v) => setForm({ ...form, signer_relationship: v })}
              placeholder="Brother, mate, colleague…"
            />
            <Input
              label="Signer signature (typed)"
              value={form.signer_signature}
              onChange={(v) => setForm({ ...form, signer_signature: v })}
              placeholder="Type your full name to sign"
            />
            <label className="flex flex-col text-sm text-slate-300">
              Notes
              <textarea
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
                rows={3}
                className="mt-1 rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-white"
              />
            </label>
            {error ? <p className="text-sm text-rose-300">{error}</p> : null}
            <button
              type="submit"
              className="rounded-full bg-cyan-500 px-5 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400"
            >
              File release
            </button>
          </form>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
            Open a conversation (outbound)
          </h2>
          <p className="mt-1 text-xs text-slate-400">
            Fires a Meta-approved WhatsApp template to a target with a release on file. Free-form
            replies from the bot are only allowed once the target responds.
          </p>
          <form onSubmit={startConversation} className="mt-4 space-y-3">
            <label className="flex flex-col text-sm text-slate-300">
              WhatsApp number
              <select
                value={launch.wa_number_id}
                onChange={(e) => setLaunch({ ...launch, wa_number_id: e.target.value })}
                className="mt-1 rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-white"
                required
              >
                <option value="">Select…</option>
                {numbers.map((n) => (
                  <option key={n.id} value={n.id}>
                    {n.label} ({n.display_number})
                  </option>
                ))}
              </select>
            </label>
            <label className="flex flex-col text-sm text-slate-300">
              Character
              <select
                value={launch.character_id}
                onChange={(e) => setLaunch({ ...launch, character_id: e.target.value })}
                className="mt-1 rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-white"
                required
              >
                <option value="">Select…</option>
                {characters.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.avatar_emoji ?? ""} {c.name}
                  </option>
                ))}
              </select>
            </label>
            <Input
              label="Target phone"
              value={launch.target_phone}
              onChange={(v) => setLaunch({ ...launch, target_phone: v })}
              placeholder="+61412345678"
            />
            <Input
              label="Template name (as approved in Meta)"
              value={launch.template_name}
              onChange={(v) => setLaunch({ ...launch, template_name: v })}
              placeholder="e.g. hello_from_a_mate"
            />
            <Input
              label="Template language code"
              value={launch.language_code}
              onChange={(v) => setLaunch({ ...launch, language_code: v })}
              placeholder="en_US"
            />
            {launchError ? <p className="text-sm text-rose-300">{launchError}</p> : null}
            <button
              type="submit"
              className="rounded-full bg-cyan-500 px-5 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400"
            >
              Send template
            </button>
          </form>
        </div>
      </section>

      <section className="rounded-2xl border border-white/10 bg-white/5 p-5">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
          On file
        </h2>
        {loading ? (
          <p className="mt-4 text-sm text-slate-500">Loading…</p>
        ) : releases.length === 0 ? (
          <p className="mt-4 text-sm text-slate-500">No releases yet.</p>
        ) : (
          <ul className="mt-4 space-y-2">
            {releases.map((r) => (
              <li
                key={r.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-white/10 bg-slate-950/50 p-3 text-sm"
              >
                <div>
                  <p className="font-medium text-white">
                    {r.target_name ?? "(unnamed)"}{" "}
                    <span className="text-slate-500">+{r.target_phone}</span>
                  </p>
                  <p className="text-xs text-slate-400">
                    Signed by {r.signer_name}
                    {r.signer_relationship ? ` (${r.signer_relationship})` : ""} ·{" "}
                    {new Date(r.signed_at).toLocaleDateString("en-AU")}
                  </p>
                </div>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs ${
                    r.revoked_at
                      ? "bg-rose-500/15 text-rose-200"
                      : "bg-emerald-500/15 text-emerald-200"
                  }`}
                >
                  {r.revoked_at ? "revoked" : "active"}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}

function Input({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <label className="flex flex-col text-sm text-slate-300">
      {label}
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="mt-1 rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-white placeholder:text-slate-600"
        required
      />
    </label>
  );
}

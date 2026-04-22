"use client";

import { useEffect, useState } from "react";
import type { WaNumber, Character } from "@/lib/comedian/types";

export default function NumbersPage() {
  const [numbers, setNumbers] = useState<WaNumber[]>([]);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({
    label: "",
    display_number: "",
    wa_phone_number_id: "",
    wa_business_account_id: "",
    default_character_id: "",
  });
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try {
      const [n, c] = await Promise.all([
        fetch("/api/numbers").then((r) => r.json()),
        fetch("/api/characters").then((r) => r.json()),
      ]);
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
    const res = await fetch("/api/numbers", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...form,
        default_character_id: form.default_character_id || null,
      }),
    });
    if (!res.ok) {
      const j = await res.json().catch(() => ({}));
      setError(j.error ?? "failed");
      return;
    }
    setForm({
      label: "",
      display_number: "",
      wa_phone_number_id: "",
      wa_business_account_id: "",
      default_character_id: "",
    });
    load();
  }

  return (
    <main className="mx-auto max-w-5xl space-y-6 px-4 py-8 sm:px-6 lg:px-8">
      <header>
        <h1 className="text-2xl font-semibold text-white">WhatsApp numbers</h1>
        <p className="mt-1 text-sm text-slate-400">
          Register the WhatsApp Business phone numbers the comedian will answer on. The{" "}
          <code className="text-cyan-200">wa_phone_number_id</code> is shown in Meta&apos;s
          WhatsApp Manager next to each number. The webhook matches inbound messages to the
          number registered here.
        </p>
      </header>

      <section className="rounded-2xl border border-white/10 bg-white/5 p-5">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300">Registered</h2>
        {loading ? (
          <p className="mt-4 text-sm text-slate-500">Loading…</p>
        ) : numbers.length === 0 ? (
          <p className="mt-4 text-sm text-slate-500">No numbers yet. Add one below.</p>
        ) : (
          <ul className="mt-4 space-y-3">
            {numbers.map((n) => {
              const ch = characters.find((c) => c.id === n.default_character_id);
              return (
                <li
                  key={n.id}
                  className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-white/10 bg-slate-950/50 p-4"
                >
                  <div>
                    <p className="font-medium text-white">{n.label}</p>
                    <p className="text-sm text-slate-400">
                      {n.display_number} &middot; id {n.wa_phone_number_id}
                    </p>
                  </div>
                  <div className="text-right text-sm">
                    <p className="text-slate-300">
                      {ch ? `${ch.avatar_emoji ?? ""} ${ch.name}` : "No character"}
                    </p>
                    <p className="text-xs text-slate-500">
                      inbound {n.inbound_enabled ? "on" : "off"} &middot; outbound{" "}
                      {n.outbound_enabled ? "on" : "off"}
                    </p>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </section>

      <section className="rounded-2xl border border-white/10 bg-white/5 p-5">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
          Register a number
        </h2>
        <form onSubmit={submit} className="mt-4 grid gap-3 sm:grid-cols-2">
          <Input
            label="Label"
            value={form.label}
            onChange={(v) => setForm({ ...form, label: v })}
            placeholder="Preston Tyre Shop"
          />
          <Input
            label="Display number"
            value={form.display_number}
            onChange={(v) => setForm({ ...form, display_number: v })}
            placeholder="+61 400 000 000"
          />
          <Input
            label="Phone number ID"
            value={form.wa_phone_number_id}
            onChange={(v) => setForm({ ...form, wa_phone_number_id: v })}
            placeholder="123456789012345"
          />
          <Input
            label="Business account ID"
            value={form.wa_business_account_id}
            onChange={(v) => setForm({ ...form, wa_business_account_id: v })}
            placeholder="987654321098765"
          />
          <label className="col-span-full flex flex-col text-sm text-slate-300">
            Default character
            <select
              value={form.default_character_id}
              onChange={(e) => setForm({ ...form, default_character_id: e.target.value })}
              className="mt-1 rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-white"
            >
              <option value="">(first active)</option>
              {characters.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.avatar_emoji ?? ""} {c.name}
                </option>
              ))}
            </select>
          </label>
          <div className="col-span-full flex items-center gap-3">
            <button
              type="submit"
              className="rounded-full bg-cyan-500 px-5 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400"
            >
              Add number
            </button>
            {error ? <span className="text-sm text-rose-300">{error}</span> : null}
          </div>
        </form>
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

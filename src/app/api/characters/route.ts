import { NextRequest, NextResponse } from "next/server";
import { getServerSupabase } from "@/lib/comedian/supabase-server";

export const runtime = "nodejs";

export async function GET() {
  const supa = getServerSupabase();
  const { data, error } = await supa
    .from("characters")
    .select("*")
    .order("created_at", { ascending: false });
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json(data ?? []);
}

export async function POST(req: NextRequest) {
  const body = (await req.json().catch(() => null)) as Record<string, unknown> | null;
  if (!body) return NextResponse.json({ error: "bad json" }, { status: 400 });
  const required = ["slug", "name", "system_prompt"];
  for (const k of required) {
    if (!body[k] || typeof body[k] !== "string") {
      return NextResponse.json({ error: `${k} required` }, { status: 400 });
    }
  }
  const supa = getServerSupabase();
  const { data, error } = await supa.from("characters").insert(body).select("*").single();
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json(data);
}

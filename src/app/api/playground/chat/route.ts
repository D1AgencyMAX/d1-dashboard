// In-browser test harness for the character brain.
// Needs only ANTHROPIC_API_KEY. No Supabase, no WhatsApp, no Meta setup.

import { NextRequest, NextResponse } from "next/server";
import { generateReply } from "@/lib/comedian/brain";
import { BRUNO_INLINE } from "@/lib/comedian/characters/bruno";
import type { Message } from "@/lib/comedian/types";

export const runtime = "nodejs";

type IncomingTurn = { role: "user" | "assistant"; content: string };
type Body = { history: IncomingTurn[]; userMessage: string };

export async function POST(req: NextRequest) {
  let body: Body;
  try {
    body = (await req.json()) as Body;
  } catch {
    return NextResponse.json({ error: "bad json" }, { status: 400 });
  }
  if (!body.userMessage || typeof body.userMessage !== "string") {
    return NextResponse.json({ error: "userMessage required" }, { status: 400 });
  }

  const history: Message[] = (body.history ?? []).map((t, i) => ({
    id: `playground-${i}`,
    conversation_id: "playground",
    direction: t.role === "user" ? "in" : "out",
    kind: "text",
    wa_message_id: null,
    text: t.content,
    transcript: null,
    audio_path: null,
    audio_duration_seconds: null,
    latency_ms: null,
    input_tokens: null,
    output_tokens: null,
    cost_usd: null,
    error: null,
    created_at: new Date().toISOString(),
  }));

  try {
    const reply = await generateReply(BRUNO_INLINE, history, body.userMessage);
    return NextResponse.json(reply);
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "brain failed" },
      { status: 500 },
    );
  }
}

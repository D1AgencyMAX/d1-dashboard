// Open a conversation with a target who has a signed release on file.
// Fires a WhatsApp template message (must be pre-approved by Meta).
// Regular free-form replies are only allowed once the target responds.

import { NextRequest, NextResponse } from "next/server";
import { getServerSupabase } from "@/lib/comedian/supabase-server";
import { sendTemplate } from "@/lib/comedian/whatsapp";
import type { OutboundRelease, WaNumber } from "@/lib/comedian/types";

export const runtime = "nodejs";

type Body = {
  wa_number_id: string;
  character_id: string;
  target_phone: string;
  template_name: string;
  language_code?: string;
  components?: unknown[];
};

export async function POST(req: NextRequest) {
  let body: Body;
  try {
    body = (await req.json()) as Body;
  } catch {
    return NextResponse.json({ error: "bad json" }, { status: 400 });
  }

  if (!body.wa_number_id || !body.character_id || !body.target_phone || !body.template_name) {
    return NextResponse.json(
      { error: "wa_number_id, character_id, target_phone, template_name are required" },
      { status: 400 },
    );
  }

  const targetPhone = normalizePhone(body.target_phone);
  const supa = getServerSupabase();

  // Verify number exists + outbound is enabled.
  const { data: num } = await supa
    .from("wa_numbers")
    .select("*")
    .eq("id", body.wa_number_id)
    .maybeSingle();
  if (!num) return NextResponse.json({ error: "number not found" }, { status: 404 });
  const waNumber = num as WaNumber;
  if (!waNumber.outbound_enabled) {
    return NextResponse.json({ error: "outbound disabled on this number" }, { status: 400 });
  }

  // Verify a valid release exists for the target.
  const { data: release } = await supa
    .from("outbound_releases")
    .select("*")
    .eq("target_phone", targetPhone)
    .is("revoked_at", null)
    .order("signed_at", { ascending: false })
    .limit(1)
    .maybeSingle();
  if (!release) {
    return NextResponse.json(
      { error: "no release on file for this target", target_phone: targetPhone },
      { status: 403 },
    );
  }
  const rel = release as OutboundRelease;
  if (rel.expires_at && new Date(rel.expires_at) < new Date()) {
    return NextResponse.json({ error: "release expired", release_id: rel.id }, { status: 403 });
  }

  // Send template.
  let waMessageId: string | null = null;
  try {
    const sent = await sendTemplate(
      waNumber.wa_phone_number_id,
      targetPhone,
      body.template_name,
      body.language_code ?? "en_US",
      body.components ?? [],
    );
    waMessageId = sent.wa_message_id;
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "send failed" },
      { status: 502 },
    );
  }

  // Open the conversation record so future inbound replies thread correctly.
  const { data: convo, error } = await supa
    .from("conversations")
    .insert({
      wa_number_id: waNumber.id,
      character_id: body.character_id,
      release_id: rel.id,
      contact_phone: targetPhone,
      contact_profile_name: rel.target_name,
      direction: "outbound",
      status: "open",
      started_at: new Date().toISOString(),
      last_message_at: new Date().toISOString(),
    })
    .select("*")
    .single();
  if (error) {
    return NextResponse.json({ error: `conversation insert failed: ${error.message}` }, { status: 500 });
  }

  await supa.from("messages").insert({
    conversation_id: convo!.id,
    direction: "out",
    kind: "system",
    wa_message_id: waMessageId,
    text: `(template sent: ${body.template_name})`,
  });

  return NextResponse.json({ conversation_id: convo!.id, wa_message_id: waMessageId });
}

function normalizePhone(raw: string): string {
  const trimmed = raw.trim().replace(/[\s\-().]/g, "");
  if (trimmed.startsWith("+")) return trimmed.slice(1);
  return trimmed;
}

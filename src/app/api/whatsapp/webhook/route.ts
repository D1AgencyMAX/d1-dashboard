// WhatsApp Business Cloud API webhook.
// GET = verification handshake. POST = message events.

import { NextRequest, NextResponse } from "next/server";
import { getServerSupabase } from "@/lib/comedian/supabase-server";
import { handleInboundMessage } from "@/lib/comedian/orchestrate";
import {
  InboundWebhookBody,
  verifySignature,
} from "@/lib/comedian/whatsapp";
import type { WaNumber } from "@/lib/comedian/types";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  const params = req.nextUrl.searchParams;
  const mode = params.get("hub.mode");
  const token = params.get("hub.verify_token");
  const challenge = params.get("hub.challenge");

  const expected = process.env.WHATSAPP_VERIFY_TOKEN;
  if (mode === "subscribe" && expected && token === expected && challenge) {
    return new NextResponse(challenge, { status: 200 });
  }
  return new NextResponse("forbidden", { status: 403 });
}

export async function POST(req: NextRequest) {
  const raw = await req.text();
  const signature = req.headers.get("x-hub-signature-256");
  const signatureOk = await verifySignature(raw, signature);
  if (!signatureOk) {
    return new NextResponse("invalid signature", { status: 401 });
  }

  let body: InboundWebhookBody;
  try {
    body = JSON.parse(raw) as InboundWebhookBody;
  } catch {
    return new NextResponse("bad json", { status: 400 });
  }

  // Respond fast so Meta doesn't retry. Process asynchronously.
  processEntries(body).catch((err) => {
    console.error("[whatsapp webhook] handler failed:", err);
  });

  return NextResponse.json({ ok: true });
}

async function processEntries(body: InboundWebhookBody) {
  const supa = getServerSupabase();
  for (const entry of body.entry ?? []) {
    for (const change of entry.changes ?? []) {
      if (change.field !== "messages") continue;
      const value = change.value;
      const phoneNumberId = value.metadata.phone_number_id;

      const { data: num } = await supa
        .from("wa_numbers")
        .select("*")
        .eq("wa_phone_number_id", phoneNumberId)
        .maybeSingle();
      if (!num) {
        console.warn(`[whatsapp webhook] no wa_number registered for phone_number_id=${phoneNumberId}`);
        continue;
      }
      const waNumber = num as WaNumber;

      for (const msg of value.messages ?? []) {
        const contact = value.contacts?.find((c) => c.wa_id === msg.from);
        await handleInboundMessage(
          waNumber,
          msg.from,
          contact?.profile?.name ?? null,
          msg,
        );
      }
    }
  }
}

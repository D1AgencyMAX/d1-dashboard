// Text -> MP3 via ElevenLabs. Used by the playground for voice playback.
import { NextRequest, NextResponse } from "next/server";
import { synthesizeSpeech } from "@/lib/comedian/voice";

export const runtime = "nodejs";

// Default = ElevenLabs preset "Callum" (hoarse, mid-age male). Override via
// ELEVENLABS_VOICE_ID in .env or pass voiceId in the request body.
const DEFAULT_VOICE_ID = "N2lVS1w4EtoT3dr4eOWO";

type Body = { text: string; voiceId?: string };

export async function POST(req: NextRequest) {
  let body: Body;
  try {
    body = (await req.json()) as Body;
  } catch {
    return NextResponse.json({ error: "bad json" }, { status: 400 });
  }
  if (!body.text || typeof body.text !== "string") {
    return NextResponse.json({ error: "text required" }, { status: 400 });
  }
  const voiceId = body.voiceId || process.env.ELEVENLABS_VOICE_ID || DEFAULT_VOICE_ID;

  try {
    const tts = await synthesizeSpeech(body.text, voiceId, "mp3");
    return new NextResponse(tts.bytes as unknown as BodyInit, {
      status: 200,
      headers: {
        "Content-Type": tts.mimeType,
        "Content-Length": String(tts.bytes.byteLength),
        "Cache-Control": "no-store",
        "X-Voice-Id": voiceId,
        "X-Cost-Usd": String(tts.costUsd),
      },
    });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "tts failed" },
      { status: 500 },
    );
  }
}
